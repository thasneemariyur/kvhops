"""
KVH Fabricator Payout controller.

Preserves the following business logic from the Lovable system:
1. Payout number: KVH/FPR/YY-YY/NNNN
2. Status workflow: Draft → Approved → Paid → Cancelled
3. Lock guard: cannot edit payout lines on Approved/Paid run (mirrors guard_payout_line_lock trigger)
4. Auto-recalculate totals on line add/remove/edit (mirrors recalc_payout_run trigger)
5. Rate from fabricator rate card (product_key → rate lookup)
6. Amount = quantity × rate (can be overridden)
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class KVHFabricatorPayout(Document):

    def before_insert(self):
        self._generate_payout_number()

    def validate(self):
        self._validate_lock_guard()
        self._recalculate_totals()

    def before_submit(self):
        if self.status not in ("Approved", "Paid"):
            frappe.throw(_("Only Approved or Paid payout runs can be submitted."))

    def on_update(self):
        self._recalculate_totals()

    def _generate_payout_number(self):
        """Generate KVH/FPR/YY-YY/NNNN payout run number."""
        if self.run_number:
            return
        from kvh_ops.utils.naming import next_fy_id, PREFIX_FABRICATOR_PAYOUT
        self.run_number = next_fy_id(PREFIX_FABRICATOR_PAYOUT)

    def _validate_lock_guard(self):
        """
        Prevent editing payout lines on Approved/Paid runs.
        Mirrors: guard_payout_line_lock trigger.
        """
        if self.is_new():
            return

        old_status = self.get_db_value("status")
        if old_status in ("Approved", "Paid") and self.status in ("Approved", "Paid"):
            # Check if any line data changed
            if self.has_value_changed("payout_items"):
                frappe.throw(
                    _("Cannot modify payout lines: run {0} is in '{1}' status. "
                      "Cancel the run first to make changes.").format(self.run_number, old_status)
                )

    def _recalculate_totals(self):
        """
        Recalculate payout run totals from line items.
        Mirrors: recalc_payout_run trigger.
        """
        total_items = 0
        total_qty = 0.0
        total_amount = 0.0

        for line in self.payout_items or []:
            # Auto-compute amount = qty × rate (unless manually overridden)
            rate = flt(line.rate_override) if line.rate_override else flt(line.rate)
            qty = flt(line.quantity)
            line.amount = flt(qty * rate, 2)

            total_items += 1
            total_qty += qty
            total_amount += line.amount

        self.total_items = total_items
        self.total_qty = flt(total_qty, 3)
        self.total_amount = flt(total_amount, 2)

    @frappe.whitelist()
    def approve(self):
        """Transition payout from Draft to Approved."""
        allowed_roles = ["KVH Admin", "KVH Production Head"]
        if not any(frappe.has_role(r) for r in allowed_roles):
            frappe.throw(_("Only Production Head or Admin can approve payout runs."))

        if self.status != "Draft":
            frappe.throw(_("Only Draft payouts can be approved."))

        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_at = now_datetime()
        self.save()

    @frappe.whitelist()
    def mark_paid(self, paid_reference=""):
        """Transition payout from Approved to Paid."""
        allowed_roles = ["KVH Admin", "KVH Production Head"]
        if not any(frappe.has_role(r) for r in allowed_roles):
            frappe.throw(_("Only Production Head or Admin can mark payouts as paid."))

        if self.status != "Approved":
            frappe.throw(_("Only Approved payouts can be marked as Paid."))

        self.status = "Paid"
        self.paid_at = now_datetime()
        self.paid_reference = paid_reference
        self.save()

    @frappe.whitelist()
    def auto_populate_lines(self):
        """
        Auto-populate payout lines from completed job cards for this fabricator
        in the specified period. Mirrors the 'Auto' mode in Lovable.
        """
        if self.mode != "Auto":
            frappe.throw(_("Auto-populate only works in Auto mode."))

        if self.status != "Draft":
            frappe.throw(_("Can only auto-populate Draft payout runs."))

        if not self.fabricator or not self.period_start or not self.period_end:
            frappe.throw(_("Fabricator, Period Start and Period End are required for auto-populate."))

        # Find completed job cards for this fabricator in the period
        completed_cards = frappe.db.sql(
            """
            SELECT
                jc.name, jc.sales_order, jc.product_description,
                jc.quantity, jc.fabricator_name, jc.stage_updated_at
            FROM `tabKVH Job Card` jc
            WHERE jc.fabricator = %s
              AND jc.factory_stage IN ('Accessories', 'Ready', 'Dispatched')
              AND jc.stage_updated_at BETWEEN %s AND %s
              AND jc.docstatus = 1
              AND NOT EXISTS (
                SELECT 1 FROM `tabKVH Fabricator Payout Item` pi
                WHERE pi.job_card = jc.name
                  AND pi.parent != %s
              )
            """,
            (self.fabricator, self.period_start, self.period_end, self.name or ""),
            as_dict=True,
        )

        lines_added = 0
        for card in completed_cards:
            # Look up rate from rate card
            rate = _lookup_rate(card.product_description)

            self.append("payout_items", {
                "job_card": card.name,
                "sales_order": card.sales_order,
                "product_description": card.product_description,
                "product_key": _normalize_product_key(card.product_description),
                "quantity": card.quantity,
                "rate": rate,
                "completed_at": card.stage_updated_at,
            })
            lines_added += 1

        self._recalculate_totals()
        self.save()

        return {"lines_added": lines_added}


def _lookup_rate(product_description):
    """Look up fabricator rate from rate card by product_key."""
    product_key = _normalize_product_key(product_description)
    rate = frappe.db.get_value(
        "KVH Fabricator Rate Card",
        {"product_key": product_key, "active": 1},
        "rate",
    )
    return flt(rate, 2)


def _normalize_product_key(description):
    """
    Normalize product description to a key for rate card lookup.
    Mirrors: product_key normalization in fabricator_rate_card table.
    lowercase, collapse whitespace.
    """
    import re
    key = (description or "").lower().strip()
    key = re.sub(r'\s+', ' ', key)
    return key
