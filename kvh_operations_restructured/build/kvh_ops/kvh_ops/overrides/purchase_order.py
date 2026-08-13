"""
Purchase Order override for KVH Operations.

Preserves the following business logic from the Lovable system:
1. Auto-create stock inward transactions when PO reaches 'MRN_Generated' status
2. Auto-generate MRN number (KVH/MRN/YY-YY/NNNN) on MRN_Generated
3. Payment status recalculation (mirrors recalc_po_payment trigger)
4. Payment status: Pending → Partial → Paid
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


def on_submit(doc, method):
    """On PO submit - set initial payment status."""
    frappe.db.set_value("Purchase Order", doc.name, "kvh_payment_status", "Pending")


def on_update_after_submit(doc, method):
    """Handle PO status changes after submit (MRN_Generated, Received)."""
    old_status = doc.get_db_value("kvh_po_status") or ""

    if doc.get("kvh_po_status") == "MRN_Generated" and old_status != "MRN_Generated":
        _generate_mrn_number(doc)
        _create_stock_inward(doc)

    _recalculate_payment_status(doc)


def _generate_mrn_number(doc):
    """
    Generate MRN number on status change to MRN_Generated.
    Mirrors: assign_mrn_number trigger and next_fy_id('MRN') function.
    """
    if doc.get("kvh_mrn_number"):
        return  # Already assigned

    from kvh_ops.utils.naming import next_fy_id, PREFIX_MRN
    mrn = next_fy_id(PREFIX_MRN)
    frappe.db.set_value("Purchase Order", doc.name, "kvh_mrn_number", mrn)
    frappe.msgprint(f"MRN Generated: {mrn}", alert=True)


def _create_stock_inward(doc):
    """
    Auto-create stock inward (Stock Entry) when PO becomes MRN_Generated.
    Mirrors: auto_inward_po trigger and apply_material_txn trigger.
    """
    # Check if stock entry already created for this PO
    existing = frappe.db.exists("Stock Entry", {
        "purchase_order": doc.name,
        "stock_entry_type": "Material Receipt",
        "docstatus": ["!=", 2],
    })

    if existing:
        return

    try:
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Receipt"
        se.purchase_order = doc.name
        se.company = doc.company
        se.posting_date = frappe.utils.today()
        se.remarks = f"Auto-inward for PO {doc.name} (MRN: {doc.get('kvh_mrn_number', '')})"

        warehouse = (
            frappe.db.get_single_value("Stock Settings", "default_warehouse")
            or frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
        )

        for item in doc.items:
            se.append("items", {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": item.qty,
                "t_warehouse": warehouse,
                "basic_rate": item.rate,
                "amount": item.amount,
                "uom": item.uom,
                "purchase_order_item": item.name,
            })

        se.insert(ignore_permissions=True)
        se.submit()

        frappe.msgprint(
            f"Stock Entry {se.name} created for material receipt.",
            alert=True
        )

    except Exception as e:
        frappe.log_error(f"Auto stock inward failed for PO {doc.name}: {e}", "KVH PO Override")
        frappe.msgprint(
            _("Warning: Could not auto-create stock inward. Please create manually.\nError: {0}").format(str(e)),
            indicator="orange"
        )


def _recalculate_payment_status(doc):
    """
    Recalculate PO payment status based on total payments vs PO amount.
    Mirrors: recalc_po_payment trigger.

    Status:
    - Pending: no payments made
    - Partial: payments made but total < PO amount
    - Paid: total payments >= PO amount
    """
    po_amount = flt(doc.grand_total)

    total_paid = frappe.db.sql(
        """
        SELECT COALESCE(SUM(paid_amount), 0) as total
        FROM `tabPayment Entry`
        WHERE reference_name = %s
          AND docstatus = 1
          AND payment_type = 'Pay'
        """,
        doc.name,
    )[0][0] or 0

    if flt(total_paid) <= 0:
        new_status = "Pending"
    elif flt(total_paid) >= po_amount and po_amount > 0:
        new_status = "Paid"
    else:
        new_status = "Partial"

    current_status = doc.get("kvh_payment_status") or ""
    if new_status != current_status:
        frappe.db.set_value("Purchase Order", doc.name, "kvh_payment_status", new_status)
