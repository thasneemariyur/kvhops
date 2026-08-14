import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate


class KVHJobCard(Document):
    """
    KVH Job Card - tracks individual production items through design and factory stages.

    Maps to: order_items table in Lovable system
    Key business logic preserved from original system:
    - factory_stage progression: Pending → CNC → Fabrication → Surface Finishing → Primer Coating →
      Powder Coating → PU Foam Filling → Accessories → Packing → Installation → Ready → Dispatched
    - design_status progression: Pending → In Progress → Hold → Completed
    - Auto-advances parent Sales Order when all items reach final stage
    - Stage events are logged to KVH Stage Event
    """

    def validate(self):
        self.validate_stage_progression()
        self.validate_design_status()

    def before_save(self):
        if self.has_value_changed("factory_stage"):
            self.stage_updated_at = now_datetime()
            self.stage_updated_by = frappe.session.user

        if self.has_value_changed("design_status") and self.design_status == "Completed":
            if not self.design_completed_at:
                self.design_completed_at = now_datetime()

    def on_update(self):
        if self.has_value_changed("factory_stage"):
            self.log_stage_event("factory", self.get_db_value("factory_stage"), self.factory_stage)
            self.check_order_completion()

        if self.has_value_changed("design_status"):
            self.log_stage_event("design", self.get_db_value("design_status"), self.design_status)

        if self.has_value_changed("designer_assigned_to") and self.designer_assigned_to:
            self.log_assignment_event("Design", self.designer_assigned_to)

        if self.has_value_changed("fabricator_name") and self.fabricator_name:
            self.log_assignment_event("Fabrication", None, self.fabricator_name)

    def validate_stage_progression(self):
        """Validate factory stage is a valid value."""
        valid_stages = [
            "Pending", "CNC", "Fabrication", "Surface Finishing", "Primer Coating",
            "Powder Coating", "PU Foam Filling", "Accessories", "Packing",
            "Installation", "Ready", "Dispatched"
        ]
        if self.factory_stage and self.factory_stage not in valid_stages:
            frappe.throw(_("Invalid factory stage: {0}").format(self.factory_stage))

    def validate_design_status(self):
        """Validate design status is a valid value."""
        valid_statuses = ["Pending", "In Progress", "Hold", "Completed"]
        if self.design_status and self.design_status not in valid_statuses:
            frappe.throw(_("Invalid design status: {0}").format(self.design_status))

    def log_stage_event(self, event_type, from_stage, to_stage):
        """Log a stage transition event to KVH Stage Event."""
        try:
            event = frappe.new_doc("KVH Stage Event")
            event.job_card = self.name
            event.sales_order = self.sales_order
            event.event_type = event_type
            event.from_stage = from_stage or ""
            event.to_stage = to_stage or ""
            event.event_kind = "stage_change"
            event.actor = frappe.session.user
            event.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log stage event: {e}", "KVH Job Card")

    def log_assignment_event(self, stage, assignee_id=None, assignee_name=None):
        """Log an assignment event to KVH Stage Event."""
        try:
            event = frappe.new_doc("KVH Stage Event")
            event.job_card = self.name
            event.sales_order = self.sales_order
            event.event_type = "assignment"
            event.stage = stage
            event.event_kind = "assigned"
            event.assignee = assignee_id
            event.assignee_name = assignee_name
            event.actor = frappe.session.user
            event.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log assignment event: {e}", "KVH Job Card")

    def check_order_completion(self):
        """
        Auto-advance Sales Order when all job cards reach a final stage.
        Preserves: auto_advance_order_status trigger from Lovable system.
        Final stages: Accessories, Installation, Ready, Dispatched
        """
        if not self.sales_order:
            return

        final_stages = {"Accessories", "Installation", "Ready", "Dispatched"}
        if self.factory_stage not in final_stages:
            return

        # Check if all job cards for this order are in final stages
        all_cards = frappe.get_all(
            "KVH Job Card",
            filters={"sales_order": self.sales_order, "docstatus": ["!=", 2]},
            fields=["name", "factory_stage"]
        )

        if not all_cards:
            return

        pending_cards = [c for c in all_cards if c.factory_stage not in final_stages]

        if pending_cards:
            return  # Not all done yet

        # All done - advance order status
        so = frappe.get_doc("Sales Order", self.sales_order)
        include_installation = so.get("include_installation", 0)

        if include_installation:
            new_status = "Ready for Installation"
            notif_title = "Order ready for installation — collect final amount"
        else:
            new_status = "Ready for Delivery"
            notif_title = "Order ready for delivery — collect final amount"

        current_so_status = so.get("kvh_production_status")
        if current_so_status != new_status:
            frappe.db.set_value("Sales Order", self.sales_order, "kvh_production_status", new_status)

            # Notify the sales person
            sales_person = so.owner
            if sales_person:
                total_amount = so.grand_total or 0
                amount_received = so.get("advance_paid", 0) or 0
                balance = max(total_amount - amount_received, 0)

                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": notif_title,
                    "email_content": f"Order {self.sales_order} for {so.customer_name} — balance ₹{balance:,.2f}",
                    "for_user": sales_person,
                    "type": "Alert",
                    "document_type": "Sales Order",
                    "document_name": self.sales_order,
                }).insert(ignore_permissions=True)


@frappe.whitelist()
def get_job_cards_for_order(sales_order):
    """Get all job cards for a sales order with current stages."""
    return frappe.get_all(
        "KVH Job Card",
        filters={"sales_order": sales_order, "docstatus": ["!=", 2]},
        fields=[
            "name", "product_description", "quantity", "design_status",
            "factory_stage", "designer_assigned_to", "fabricator_name",
            "sheet_spec", "grill_spec", "installation_method"
        ],
        order_by="creation asc"
    )


@frappe.whitelist()
def bulk_update_factory_stage(job_cards, new_stage):
    """Bulk update factory stage for multiple job cards."""
    if not frappe.has_permission("KVH Job Card", "write"):
        frappe.throw(_("No permission to update Job Cards"))

    cards = frappe.parse_json(job_cards) if isinstance(job_cards, str) else job_cards
    updated = 0

    for card_name in cards:
        try:
            card = frappe.get_doc("KVH Job Card", card_name)
            card.factory_stage = new_stage
            card.save()
            updated += 1
        except Exception as e:
            frappe.log_error(f"Failed to update {card_name}: {e}", "KVH Job Card Bulk Update")

    return {"updated": updated, "total": len(cards)}
