"""
CRM Lead override for KVH Operations.

Preserves the following business logic from the Lovable system:
1. Phone normalization: extract last 10 digits from phone number → phone_norm
2. Duplicate detection: flag as duplicate if another lead with same phone_norm exists
3. Auto-assignment round-robin to CRE users (preserves leads_auto_assign trigger)
4. Lead number generation: KVH/LEAD/YY-YY/NNNN
5. Stage activity logging (stage_change, owner_change events)
6. Follow-up sync: next_followup_at auto-updated when follow-ups change
7. last_contacted_at auto-updated when a call is logged

Custom fields added to CRM Lead:
- phone_norm: Data (normalized 10-digit phone)
- is_duplicate: Check
- merged_into: Link to CRM Lead
- ai_summary: Long Text
- ai_summary_updated_at: Datetime
- location_lat: Float
- location_lng: Float
- location_url: Data
- converted_order: Link to Sales Order
- lead_number: Data (KVH/LEAD/YY-YY/NNNN)
- next_followup_at: Datetime
- last_contacted_at: Datetime
- branch: Link to Branch
- place: Data
"""

import re
import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime


def before_insert(doc, method):
    """Before insert: generate lead number, normalize phone, detect duplicate."""
    _generate_lead_number(doc)
    _normalize_phone(doc)
    _detect_duplicate(doc)
    _auto_assign(doc)


def before_save(doc, method):
    """Before save: normalize phone, update phone_norm."""
    _normalize_phone(doc)


def after_insert(doc, method):
    """After insert: log lead created activity."""
    _log_activity(doc, "lead_created", to_value=doc.lead_stage or "New",
                  body=f"Lead created from {doc.source or 'Manual'}")


def on_update(doc, method):
    """On update: log stage changes and owner changes."""
    # Log stage change
    if doc.has_value_changed("lead_stage"):
        _log_activity(
            doc, "stage_change",
            from_value=doc.get_db_value("lead_stage"),
            to_value=doc.lead_stage,
        )

    # Log owner change
    if doc.has_value_changed("lead_owner"):
        _log_activity(
            doc, "owner_change",
            from_value=doc.get_db_value("lead_owner") or "",
            to_value=doc.lead_owner or "",
        )

    # Re-normalize phone if changed
    if doc.has_value_changed("mobile_no") or doc.has_value_changed("phone"):
        _normalize_phone(doc)
        if doc.get("is_new") is False:
            doc.db_update()


def _generate_lead_number(doc):
    """Generate KVH/LEAD/YY-YY/NNNN number if not set."""
    if doc.get("lead_number"):
        return

    from kvh_ops.utils.naming import next_fy_id
    doc.lead_number = next_fy_id("LEAD")


def _normalize_phone(doc):
    """
    Normalize phone number to last 10 digits.
    Preserves: leads_before_insupd trigger phone normalization.
    """
    phone = doc.mobile_no or doc.phone or ""
    digits = re.sub(r'\D', '', phone)

    if len(digits) >= 10:
        doc.phone_norm = digits[-10:]
    elif digits:
        doc.phone_norm = digits
    else:
        doc.phone_norm = None


def _detect_duplicate(doc):
    """
    Detect duplicate leads by normalized phone number.
    Preserves: duplicate detection in leads_before_insupd trigger.
    """
    if not doc.get("phone_norm") or len(doc.phone_norm) < 10:
        return

    existing = frappe.db.exists(
        "CRM Lead",
        {
            "phone_norm": doc.phone_norm,
            "name": ["!=", doc.name or ""],
            "merged_into": ["is", "not set"],
        }
    )

    if existing:
        doc.is_duplicate = 1
    else:
        doc.is_duplicate = 0


def _auto_assign(doc):
    """
    Round-robin auto-assign lead to CRE users.
    Preserves: leads_auto_assign trigger logic.

    Uses a singleton record to track last assigned user.
    """
    if doc.lead_owner:
        return  # Already has owner

    # Get all active CRE users ordered by user ID
    cre_users = frappe.get_all(
        "Has Role",
        filters={"role": "KVH CRE", "parenttype": "User"},
        fields=["parent"],
        distinct=True,
        order_by="parent asc",
    )

    if not cre_users:
        return

    cre_ids = [u.parent for u in cre_users]

    # Check only active users
    active_cres = frappe.get_all(
        "User",
        filters={"name": ("in", cre_ids), "enabled": 1},
        fields=["name"],
        order_by="name asc",
    )

    if not active_cres:
        return

    active_ids = [u.name for u in active_cres]

    # Get last assigned user
    last_assigned = frappe.db.get_single_value("KVH Lead Assignment State", "last_assigned_user") or ""

    # Find next in round-robin order
    next_user = None
    if last_assigned:
        after = [u for u in active_ids if u > last_assigned]
        next_user = after[0] if after else active_ids[0]
    else:
        next_user = active_ids[0]

    if next_user:
        doc.lead_owner = next_user
        # Update last assigned
        try:
            frappe.db.set_single_value("KVH Lead Assignment State", "last_assigned_user", next_user)
        except Exception:
            pass


def _log_activity(doc, activity_type, from_value="", to_value="", body=""):
    """Log a lead activity record."""
    try:
        activity = frappe.new_doc("CRM Note")
        activity.reference_doctype = "CRM Lead"
        activity.reference_docname = doc.name
        activity.note = body or f"{activity_type}: {from_value} → {to_value}"
        activity.added_by = frappe.session.user
        activity.insert(ignore_permissions=True)
    except Exception as e:
        # Don't fail the main operation for activity log failures
        frappe.log_error(f"Lead activity log failed: {e}", "CRM Lead Override")


@frappe.whitelist()
def log_call(lead, direction, outcome, duration_sec=0, notes=""):
    """
    Log a call against a lead.
    Preserves: lead_calls table and lead_call_bump_contact trigger.
    """
    if not frappe.has_permission("CRM Lead", "write"):
        frappe.throw(_("No permission to log calls."))

    call = frappe.new_doc("CRM Call Log")
    call.reference_doctype = "CRM Lead"
    call.reference_docname = lead
    call.type = direction
    call.outcome = outcome
    call.duration = int(duration_sec)
    call.note = notes
    call.insert(ignore_permissions=True)

    # Update last_contacted_at (preserves lead_call_bump_contact trigger)
    frappe.db.set_value("CRM Lead", lead, "last_contacted_at", now_datetime())

    return {"name": call.name}


@frappe.whitelist()
def log_followup(lead, due_at, note="", assignee=None):
    """
    Log a follow-up against a lead.
    Preserves: lead_followups table and lead_followup_sync trigger.
    """
    followup = frappe.new_doc("CRM Appointment")
    followup.lead = lead
    followup.scheduled_time = due_at
    followup.notes = note
    if assignee:
        followup.assigned_to = assignee
    followup.insert(ignore_permissions=True)

    # Update next_followup_at on lead (preserves lead_followup_sync trigger)
    _sync_next_followup(lead)

    return {"name": followup.name}


def _sync_next_followup(lead_name):
    """Sync next_followup_at on lead from pending follow-ups."""
    next_due = frappe.db.get_value(
        "CRM Appointment",
        {"lead": lead_name, "status": ("not in", ["Closed", "Cancelled"])},
        "min(scheduled_time)",
    )
    frappe.db.set_value("CRM Lead", lead_name, "next_followup_at", next_due)


@frappe.whitelist()
def generate_ai_summary(lead):
    """
    Generate AI summary for a lead.
    Preserves: ai_summary field in leads table.
    """
    try:
        from kvh_ops.utils.ai import generate_lead_summary
        lead_doc = frappe.get_doc("CRM Lead", lead)
        summary = generate_lead_summary(lead_doc)

        frappe.db.set_value("CRM Lead", lead, {
            "ai_summary": summary,
            "ai_summary_updated_at": now_datetime(),
        })

        return {"summary": summary}
    except Exception as e:
        frappe.log_error(f"AI summary generation failed: {e}", "CRM Lead AI")
        frappe.throw(_("AI summary generation failed. Please try again."))


@frappe.whitelist()
def merge_leads(primary_lead, duplicate_lead):
    """
    Merge a duplicate lead into a primary lead.
    Preserves: merged_into_id field and merge workflow.
    """
    allowed_roles = ["KVH Admin", "KVH Sales Head", "KVH BDM"]
    if not any(frappe.has_role(r) for r in allowed_roles):
        frappe.throw(_("Only Admin, Sales Head or BDM can merge leads."))

    frappe.db.set_value("CRM Lead", duplicate_lead, {
        "merged_into": primary_lead,
        "is_duplicate": 1,
        "lead_stage": "lost",
    })

    return {"success": True, "message": _(f"Lead {duplicate_lead} merged into {primary_lead}")}
