"""
Sales Order override for KVH Operations.

Preserves the following business logic from the Lovable system:
1. Payment gate: order is blocked at 'Payment Pending' if advance < 35% of total
2. Payment status auto-calculation: Payment Pending → Advance Received → Fully Paid
3. Override approval: Admin/Sales_Head/BDM can bypass the 35% payment gate
4. Auto-advance order production status when all job cards complete
5. Order cancellation with reason and timestamp
6. CRE edit request workflow (requires approval before CRE can edit submitted order)

Custom fields added to Sales Order:
- kvh_finish_type: Select (Primer Finish / Powder Coating)
- include_installation: Check
- override_approved_by: Link to User
- override_approved_at: Datetime
- kvh_payment_status: Select (Payment Pending / Advance Received / Fully Paid)
- kvh_production_status: Select (production pipeline status)
- cancellation_reason: Small Text
- cancelled_by_user: Link to User
- branch: Link to Branch
- committed_delivery_date: Date
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, getdate


def validate(doc, method):
    """Validate Sales Order - enforce payment gate and compute payment status."""
    _compute_payment_status(doc)
    _enforce_payment_gate(doc)
    _validate_custom_fields(doc)


def before_submit(doc, method):
    """Before submit validations."""
    if doc.get("kvh_payment_status") == "Payment Pending":
        override_approved_by = doc.get("override_approved_by")
        if not override_approved_by:
            frappe.throw(
                _("Cannot submit order: Payment is pending (less than 35% advance received). "
                  "Either collect advance or get an override approval from Admin/Sales Head/BDM."),
                title=_("Payment Gate")
            )


def on_submit(doc, method):
    """On submit: create job cards for each order item."""
    _create_job_cards(doc)
    _send_design_team_notification(doc)


def on_cancel(doc, method):
    """On cancel: record cancellation details."""
    if not doc.get("cancellation_reason"):
        frappe.throw(_("Please provide a cancellation reason before cancelling this order."))

    frappe.db.set_value("Sales Order", doc.name, {
        "cancelled_by_user": frappe.session.user,
        "cancellation_date": now_datetime().date(),
    })

    # Notify the sales person
    if doc.owner:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": _("Order Cancelled"),
            "email_content": _(
                "Order {0} for {1} was cancelled. Reason: {2}"
            ).format(doc.name, doc.customer_name, doc.get("cancellation_reason", "—")),
            "for_user": doc.owner,
            "type": "Alert",
            "document_type": "Sales Order",
            "document_name": doc.name,
        }).insert(ignore_permissions=True)


def _compute_payment_status(doc):
    """
    Compute payment status based on advance payment percentage.
    Mirrors the enforce_payment_gate() PostgreSQL trigger logic.

    Rules:
    - Fully Paid: amount_received >= total_amount (and total > 0)
    - Advance Received: (amount_received / total_amount) >= 35%
    - Payment Pending: otherwise
    """
    total_amount = flt(doc.grand_total) or flt(doc.get("total_amount", 0))
    amount_received = flt(doc.get("advance_paid", 0)) or flt(doc.get("amount_received", 0))

    if total_amount <= 0:
        pct = 0
    else:
        pct = (amount_received / total_amount) * 100

    if amount_received >= total_amount and total_amount > 0:
        doc.set("kvh_payment_status", "Fully Paid")
    elif pct >= 35:
        doc.set("kvh_payment_status", "Advance Received")
    else:
        doc.set("kvh_payment_status", "Payment Pending")


def _enforce_payment_gate(doc):
    """
    Enforce the 35% payment gate on order status.
    If payment is pending and no override, set production status to Payment Pending.
    If payment is received, allow progression to Pending Design.
    """
    current_kvh_status = doc.get("kvh_production_status") or "Payment Pending"
    payment_status = doc.get("kvh_payment_status")
    override_approved_by = doc.get("override_approved_by")

    if payment_status == "Payment Pending" and not override_approved_by:
        # Block at Payment Pending
        if current_kvh_status in ("Payment Pending", "Pending Design") or not current_kvh_status:
            doc.set("kvh_production_status", "Payment Pending")
    else:
        # Payment received or overridden - allow Pending Design
        if current_kvh_status == "Payment Pending":
            doc.set("kvh_production_status", "Pending Design")


def _validate_custom_fields(doc):
    """Validate KVH-specific custom fields."""
    valid_finish_types = ["Primer Finish", "Powder Coating", ""]
    if doc.get("kvh_finish_type") and doc.get("kvh_finish_type") not in valid_finish_types:
        frappe.throw(_("Invalid finish type: {0}").format(doc.get("kvh_finish_type")))


def _create_job_cards(doc):
    """
    Create KVH Job Cards for each order item on Sales Order submission.
    Each item in the order becomes a Job Card for production tracking.
    """
    for item in doc.items:
        # Check if job card already exists for this item
        existing = frappe.db.exists("KVH Job Card", {
            "sales_order": doc.name,
            "product_description": item.item_name or item.description,
        })

        if existing:
            continue

        job_card = frappe.new_doc("KVH Job Card")
        job_card.sales_order = doc.name
        job_card.customer = doc.customer
        job_card.customer_name = doc.customer_name
        job_card.order_date = doc.transaction_date
        job_card.committed_delivery_date = doc.get("committed_delivery_date") or doc.delivery_date
        job_card.branch = doc.get("branch")
        job_card.finish_type = doc.get("kvh_finish_type") or "Primer Finish"
        job_card.include_installation = doc.get("include_installation", 0)
        job_card.product_description = item.item_name or item.description or item.item_code
        job_card.quantity = int(item.qty)
        job_card.sheet_spec = item.get("sheet_spec", "")
        job_card.grill_spec = item.get("grill_spec", "")
        job_card.installation_method = item.get("installation_method", "")
        job_card.design_status = "Pending"
        job_card.factory_stage = "Pending"
        job_card.status = "Pending Design"
        job_card.insert(ignore_permissions=True)


def _send_design_team_notification(doc):
    """Notify Design Team of new order requiring design work."""
    design_team_users = frappe.get_all(
        "Has Role",
        filters={"role": "KVH Design Team", "parenttype": "User"},
        fields=["parent"],
    )

    for user in design_team_users:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": _("New order requires design: {0}").format(doc.name),
                "email_content": _(
                    "Order {0} for {1} (₹{2}) has been submitted and requires design assignment."
                ).format(doc.name, doc.customer_name, doc.grand_total),
                "for_user": user.parent,
                "type": "Alert",
                "document_type": "Sales Order",
                "document_name": doc.name,
            }).insert(ignore_permissions=True)
        except Exception:
            pass


@frappe.whitelist()
def approve_payment_override(sales_order, reason=""):
    """
    Allow Admin/Sales_Head/BDM to bypass the 35% payment gate.
    Preserves: override_approved_by / override_approved_at logic.
    """
    allowed_roles = ["KVH Admin", "KVH Sales Head", "KVH BDM"]
    if not any(frappe.has_role(r) for r in allowed_roles):
        frappe.throw(_("Only Admin, Sales Head or BDM can approve payment overrides."))

    frappe.db.set_value("Sales Order", sales_order, {
        "override_approved_by": frappe.session.user,
        "override_approved_at": now_datetime(),
    })

    # Trigger re-evaluation of payment gate
    doc = frappe.get_doc("Sales Order", sales_order)
    if doc.get("kvh_production_status") == "Payment Pending":
        frappe.db.set_value("Sales Order", sales_order, "kvh_production_status", "Pending Design")

    frappe.db.commit()
    return {"success": True, "message": _("Payment override approved for order {0}").format(sales_order)}


@frappe.whitelist()
def request_order_edit(sales_order, reason):
    """
    CRE requests edit permission for a submitted sales order.
    Preserves: order_edit_requests workflow.
    """
    if not frappe.has_role("KVH CRE"):
        frappe.throw(_("Only CRE users can request order edit permission."))

    so = frappe.get_doc("Sales Order", sales_order)
    if so.owner != frappe.session.user:
        frappe.throw(_("You can only request edit permission for your own orders."))

    edit_request = frappe.new_doc("KVH Order Edit Request")
    edit_request.sales_order = sales_order
    edit_request.requested_by = frappe.session.user
    edit_request.reason = reason
    edit_request.status = "Pending"
    edit_request.insert(ignore_permissions=True)

    # Notify approvers
    _notify_edit_request_approvers(edit_request.name, sales_order, so.customer_name, reason)

    return {"name": edit_request.name}


def _notify_edit_request_approvers(request_name, sales_order, customer_name, reason):
    """Notify Admin/Sales_Head/BDM of edit request."""
    approver_roles = ["KVH Admin", "KVH Sales Head", "KVH BDM"]
    approvers = frappe.get_all(
        "Has Role",
        filters={"role": ("in", approver_roles), "parenttype": "User"},
        fields=["parent"],
        distinct=True,
    )

    requester_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

    for approver in approvers:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": _("Edit permission requested for order {0}").format(sales_order),
                "email_content": _(
                    "{0} requested to edit order {1} ({2}). Reason: {3}"
                ).format(requester_name, sales_order, customer_name, reason or "—"),
                "for_user": approver.parent,
                "type": "Alert",
                "document_type": "KVH Order Edit Request",
                "document_name": request_name,
            }).insert(ignore_permissions=True)
        except Exception:
            pass
