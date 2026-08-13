import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime


class KVHOrderEditRequest(Document):

    def validate(self):
        if self.is_new():
            self.status = "Pending"
            self.requested_by = frappe.session.user

    def after_insert(self):
        """Notify approvers when a new edit request is created."""
        self._notify_approvers()

    def on_update(self):
        """Notify requester when request is decided."""
        if self.has_value_changed("status") and self.status in ("Approved", "Rejected"):
            self.decided_by = frappe.session.user
            self.decided_at = now_datetime()
            self.db_update()
            self._notify_requester()

    def _notify_approvers(self):
        """Notify Admin/Sales_Head/BDM of new edit request."""
        approver_roles = ["KVH Admin", "KVH Sales Head", "KVH BDM"]
        approvers = frappe.get_all(
            "Has Role",
            filters={"role": ("in", approver_roles), "parenttype": "User"},
            fields=["parent"],
            distinct=True,
        )

        so_customer = frappe.db.get_value("Sales Order", self.sales_order, "customer_name") or ""
        requester_name = frappe.db.get_value("User", self.requested_by, "full_name") or self.requested_by

        for approver in approvers:
            if approver.parent == self.requested_by:
                continue
            try:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": _("Edit permission requested for {0}").format(self.sales_order),
                    "email_content": _(
                        "{0} requested to edit order {1} ({2}). Reason: {3}"
                    ).format(requester_name, self.sales_order, so_customer, self.reason or "—"),
                    "for_user": approver.parent,
                    "type": "Alert",
                    "document_type": "KVH Order Edit Request",
                    "document_name": self.name,
                }).insert(ignore_permissions=True)
            except Exception:
                pass

    def _notify_requester(self):
        """Notify the requester of the decision."""
        if self.status == "Approved":
            subject = _("Edit permission approved for {0}").format(self.sales_order)
            expiry_str = ""
            if self.approved_until:
                expiry_str = _(" until {0}").format(
                    frappe.utils.format_datetime(self.approved_until, "dd MMM HH:mm")
                )
            body = _("Order {0} — you can now edit{1}.").format(self.sales_order, expiry_str)
        else:
            subject = _("Edit permission rejected for {0}").format(self.sales_order)
            note = f": {self.decision_note}" if self.decision_note else ""
            body = _("Order {0} — request rejected{1}.").format(self.sales_order, note)

        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": body,
                "for_user": self.requested_by,
                "type": "Alert",
                "document_type": "KVH Order Edit Request",
                "document_name": self.name,
            }).insert(ignore_permissions=True)
        except Exception:
            pass


@frappe.whitelist()
def decide_edit_request(request_name, decision, decision_note="", approved_hours=24):
    """
    Approve or reject an order edit request.
    Preserves: oer_decide_mgmt RLS policy logic.
    """
    allowed_roles = ["KVH Admin", "KVH Sales Head", "KVH BDM"]
    if not any(frappe.has_role(r) for r in allowed_roles):
        frappe.throw(_("Only Admin, Sales Head or BDM can decide on edit requests."))

    request = frappe.get_doc("KVH Order Edit Request", request_name)
    if request.status != "Pending":
        frappe.throw(_("Only Pending requests can be decided."))

    request.status = decision  # 'Approved' or 'Rejected'
    request.decision_note = decision_note
    request.decided_by = frappe.session.user
    request.decided_at = now_datetime()

    if decision == "Approved":
        import frappe.utils
        approved_until = frappe.utils.add_to_date(now_datetime(), hours=int(approved_hours))
        request.approved_until = approved_until

    request.save(ignore_permissions=True)
    return {"status": request.status, "approved_until": str(request.approved_until or "")}
