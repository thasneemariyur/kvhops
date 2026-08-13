"""
Daily scheduled tasks for KVH Operations.
These replace the PostgreSQL trigger-based automations and cron jobs.
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, now_datetime, getdate


def check_overdue_deliveries():
    """
    Check for orders past committed delivery date and create alerts.
    Mirrors the delivery alerts banner in the Lovable frontend.
    """
    overdue_orders = frappe.db.sql(
        """
        SELECT
            so.name, so.customer_name, so.owner,
            so.committed_delivery_date,
            DATEDIFF(NOW(), so.committed_delivery_date) as days_overdue
        FROM `tabSales Order` so
        WHERE so.committed_delivery_date < CURDATE()
          AND so.docstatus = 1
          AND so.status NOT IN ('Completed', 'Cancelled', 'Closed')
          AND (so.kvh_production_status IS NULL
               OR so.kvh_production_status NOT IN ('Ready for Delivery', 'Ready for Installation', 'Delivered'))
          AND so.committed_delivery_date IS NOT NULL
        ORDER BY so.committed_delivery_date ASC
        LIMIT 100
        """,
        as_dict=True,
    )

    for order in overdue_orders:
        # Only notify once per day
        existing = frappe.db.exists("Notification Log", {
            "document_type": "Sales Order",
            "document_name": order.name,
            "subject": ("like", "OVERDUE%"),
            "creation": (">=", today()),
        })
        if existing:
            continue

        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"OVERDUE: Order {order.name} is {order.days_overdue} day(s) late",
                "email_content": (
                    f"Order {order.name} for {order.customer_name} was due on "
                    f"{order.committed_delivery_date} ({order.days_overdue} days ago)"
                ),
                "for_user": order.owner,
                "type": "Alert",
                "document_type": "Sales Order",
                "document_name": order.name,
            }).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Overdue delivery alert failed for {order.name}: {e}", "KVH Daily Tasks")


def check_sla_breaches():
    """
    Check for SLA breaches across active orders.
    Mirrors: admin.sla module from Lovable.
    """
    sla_rules = frappe.get_all(
        "KVH SLA Rule",
        filters={"enabled": 1},
        fields=["name", "stage", "max_hours", "notify_roles"],
    )

    for rule in sla_rules:
        # Find job cards stuck in this stage beyond max_hours
        breach_threshold = frappe.utils.add_to_date(
            now_datetime(), hours=-int(rule.max_hours)
        )

        stuck_cards = frappe.db.sql(
            """
            SELECT jc.name, jc.sales_order, jc.customer_name, jc.factory_stage,
                   jc.stage_updated_at, jc.designer_assigned_to
            FROM `tabKVH Job Card` jc
            WHERE jc.factory_stage = %s
              AND jc.stage_updated_at < %s
              AND jc.docstatus != 2
            LIMIT 50
            """,
            (rule.stage, breach_threshold),
            as_dict=True,
        )

        for card in stuck_cards:
            # Log breach
            try:
                breach = frappe.new_doc("KVH SLA Breach Log")
                breach.job_card = card.name
                breach.sales_order = card.sales_order
                breach.sla_rule = rule.name
                breach.stage = card.factory_stage
                breach.breach_detected_at = now_datetime()
                breach.insert(ignore_permissions=True)
            except Exception:
                pass


def sync_lead_followups():
    """
    Sync next_followup_at for all leads with pending follow-ups.
    Mirrors: lead_followup_sync trigger.
    """
    leads_needing_sync = frappe.db.sql(
        """
        SELECT DISTINCT ca.lead
        FROM `tabCRM Appointment` ca
        WHERE ca.lead IS NOT NULL
          AND ca.status NOT IN ('Closed', 'Cancelled')
          AND ca.scheduled_time > NOW()
        """,
        as_list=True,
    )

    for (lead_name,) in leads_needing_sync:
        try:
            next_due = frappe.db.get_value(
                "CRM Appointment",
                {"lead": lead_name, "status": ("not in", ["Closed", "Cancelled"])},
                "min(scheduled_time)",
            )
            frappe.db.set_value("CRM Lead", lead_name, "next_followup_at", next_due)
        except Exception:
            pass


def check_subscription_renewals():
    """
    Alert on upcoming marketing subscription renewals.
    Mirrors: marketing_subscriptions.next_renewal_date monitoring.
    """
    upcoming = frappe.db.sql(
        """
        SELECT ms.name, ms.vendor_name, ms.plan_name, ms.cost,
               ms.next_renewal_date, ms.billing_cycle
        FROM `tabKVH Marketing Subscription` ms
        WHERE ms.status = 'Active'
          AND ms.next_renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """,
        as_dict=True,
    )

    if not upcoming:
        return

    # Notify Marketing Head
    mkt_heads = frappe.get_all(
        "Has Role",
        filters={"role": "KVH Marketing Head", "parenttype": "User"},
        fields=["parent"],
        distinct=True,
    )

    for sub in upcoming:
        for head in mkt_heads:
            try:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": f"Subscription renewal due: {sub.vendor_name} — {sub.plan_name}",
                    "email_content": (
                        f"Subscription '{sub.plan_name}' from {sub.vendor_name} "
                        f"renews on {sub.next_renewal_date} (₹{sub.cost})"
                    ),
                    "for_user": head.parent,
                    "type": "Alert",
                    "document_type": "KVH Marketing Subscription",
                    "document_name": sub.name,
                }).insert(ignore_permissions=True)
            except Exception:
                pass


def expire_edit_requests():
    """
    Expire approved edit requests past their approved_until date.
    Mirrors: edit_request_status 'Expired' in Lovable.
    """
    frappe.db.sql(
        """
        UPDATE `tabKVH Order Edit Request`
        SET status = 'Expired'
        WHERE status = 'Approved'
          AND approved_until IS NOT NULL
          AND approved_until < NOW()
        """
    )
    frappe.db.commit()
