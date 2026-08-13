"""
Custom fields to add to standard ERPNext DocTypes for KVH Operations.
Run this as a fixture or migration script.

Maps the KVH-specific fields that were added to standard tables in the Lovable system
(via ALTER TABLE) into Frappe Custom Fields.
"""

import frappe


def create_all_custom_fields():
    """Create all custom fields on standard DocTypes."""
    create_sales_order_fields()
    create_sales_order_item_fields()
    create_crm_lead_fields()
    create_customer_fields()
    create_supplier_fields()
    create_purchase_order_fields()
    create_item_fields()
    frappe.db.commit()


def create_sales_order_fields():
    """
    Custom fields for Sales Order.
    Mirrors: fields added to public.orders table in Lovable.
    """
    fields = [
        # KVH Production/Status fields
        {
            "fieldname": "kvh_production_status",
            "label": "Production Status",
            "fieldtype": "Select",
            "options": "\nPayment Pending\nPending Design\nIn Design\nPending CNC\nIn Fabrication\nReady for Delivery\nReady for Installation\nDelivered\nCancelled",
            "default": "Payment Pending",
            "insert_after": "status",
            "bold": 1,
            "in_list_view": 1,
            "read_only": 1,
        },
        {
            "fieldname": "kvh_payment_status",
            "label": "Payment Gate Status",
            "fieldtype": "Select",
            "options": "\nPayment Pending\nAdvance Received\nFully Paid",
            "default": "Payment Pending",
            "insert_after": "kvh_production_status",
            "in_list_view": 1,
            "read_only": 1,
        },
        # Payment override
        {
            "fieldname": "override_approved_by",
            "label": "Payment Override Approved By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "kvh_payment_status",
            "read_only": 1,
        },
        {
            "fieldname": "override_approved_at",
            "label": "Payment Override Approved At",
            "fieldtype": "Datetime",
            "insert_after": "override_approved_by",
            "read_only": 1,
        },
        # KVH-specific order fields
        {
            "fieldname": "kvh_finish_type",
            "label": "Finish Type",
            "fieldtype": "Select",
            "options": "\nPrimer Finish\nPowder Coating",
            "default": "Primer Finish",
            "insert_after": "delivery_date",
        },
        {
            "fieldname": "include_installation",
            "label": "Include Installation",
            "fieldtype": "Check",
            "insert_after": "kvh_finish_type",
            "default": "0",
        },
        {
            "fieldname": "committed_delivery_date",
            "label": "Committed Delivery Date",
            "fieldtype": "Date",
            "insert_after": "include_installation",
        },
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "insert_after": "company",
        },
        # Cancellation fields
        {
            "fieldname": "cancellation_reason",
            "label": "Cancellation Reason",
            "fieldtype": "Small Text",
            "insert_after": "status",
        },
        {
            "fieldname": "cancelled_by_user",
            "label": "Cancelled By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "cancellation_reason",
            "read_only": 1,
        },
        {
            "fieldname": "cancellation_date",
            "label": "Cancelled At",
            "fieldtype": "Date",
            "insert_after": "cancelled_by_user",
            "read_only": 1,
        },
    ]
    _create_fields("Sales Order", fields)


def create_sales_order_item_fields():
    """
    Custom fields for Sales Order Item.
    Mirrors: fields on public.order_items table.
    """
    fields = [
        {
            "fieldname": "designer_assigned_to",
            "label": "Designer Assigned To",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "description",
        },
        {
            "fieldname": "fabricator_assigned_to",
            "label": "Fabricator (User)",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "designer_assigned_to",
        },
        {
            "fieldname": "fabricator_name_text",
            "label": "Fabricator Name (External)",
            "fieldtype": "Data",
            "insert_after": "fabricator_assigned_to",
        },
        {
            "fieldname": "design_status",
            "label": "Design Status",
            "fieldtype": "Select",
            "options": "Pending\nIn Progress\nHold\nCompleted",
            "default": "Pending",
            "insert_after": "fabricator_name_text",
        },
        {
            "fieldname": "factory_stage",
            "label": "Factory Stage",
            "fieldtype": "Select",
            "options": "Pending\nCNC\nFabrication\nSurface Finishing\nPrimer Coating\nPowder Coating\nPU Foam Filling\nAccessories\nPacking\nInstallation\nReady\nDispatched",
            "default": "Pending",
            "insert_after": "design_status",
        },
        {
            "fieldname": "sheet_spec",
            "label": "Sheet Specification",
            "fieldtype": "Data",
            "insert_after": "factory_stage",
        },
        {
            "fieldname": "grill_spec",
            "label": "Grill Specification",
            "fieldtype": "Data",
            "insert_after": "sheet_spec",
        },
        {
            "fieldname": "installation_method",
            "label": "Installation Method",
            "fieldtype": "Data",
            "insert_after": "grill_spec",
        },
    ]
    _create_fields("Sales Order Item", fields)


def create_crm_lead_fields():
    """
    Custom fields for CRM Lead.
    Mirrors: extra fields on public.leads table.
    """
    fields = [
        {
            "fieldname": "lead_number",
            "label": "Lead Number (KVH)",
            "fieldtype": "Data",
            "insert_after": "name",
            "read_only": 1,
            "unique": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "phone_norm",
            "label": "Normalized Phone",
            "fieldtype": "Data",
            "insert_after": "mobile_no",
            "read_only": 1,
            "description": "Last 10 digits of mobile number for duplicate detection",
        },
        {
            "fieldname": "is_duplicate",
            "label": "Is Duplicate",
            "fieldtype": "Check",
            "insert_after": "phone_norm",
            "default": "0",
        },
        {
            "fieldname": "merged_into",
            "label": "Merged Into",
            "fieldtype": "Link",
            "options": "CRM Lead",
            "insert_after": "is_duplicate",
        },
        {
            "fieldname": "ai_summary",
            "label": "AI Summary",
            "fieldtype": "Long Text",
            "insert_after": "notes",
        },
        {
            "fieldname": "ai_summary_updated_at",
            "label": "AI Summary Updated At",
            "fieldtype": "Datetime",
            "insert_after": "ai_summary",
            "read_only": 1,
        },
        {
            "fieldname": "location_lat",
            "label": "Location Latitude",
            "fieldtype": "Float",
            "insert_after": "ai_summary_updated_at",
        },
        {
            "fieldname": "location_lng",
            "label": "Location Longitude",
            "fieldtype": "Float",
            "insert_after": "location_lat",
        },
        {
            "fieldname": "location_url",
            "label": "Location URL",
            "fieldtype": "Data",
            "insert_after": "location_lng",
        },
        {
            "fieldname": "converted_order",
            "label": "Converted to Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "location_url",
            "read_only": 1,
        },
        {
            "fieldname": "next_followup_at",
            "label": "Next Follow-up At",
            "fieldtype": "Datetime",
            "insert_after": "converted_order",
            "read_only": 1,
        },
        {
            "fieldname": "last_contacted_at",
            "label": "Last Contacted At",
            "fieldtype": "Datetime",
            "insert_after": "next_followup_at",
            "read_only": 1,
        },
        {
            "fieldname": "place",
            "label": "Place / Area",
            "fieldtype": "Data",
            "insert_after": "city",
        },
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "insert_after": "place",
        },
    ]
    _create_fields("CRM Lead", fields)


def create_customer_fields():
    """Custom fields for Customer (ERPNext) to match KVH customer data."""
    fields = [
        {
            "fieldname": "customer_number_kvh",
            "label": "KVH Customer Number",
            "fieldtype": "Data",
            "insert_after": "customer_name",
            "read_only": 1,
            "unique": 1,
        },
        {
            "fieldname": "mobile_norm",
            "label": "Normalized Mobile",
            "fieldtype": "Data",
            "insert_after": "mobile_no",
            "read_only": 1,
        },
        {
            "fieldname": "district",
            "label": "District",
            "fieldtype": "Data",
            "insert_after": "city",
        },
        {
            "fieldname": "customer_type_kvh",
            "label": "Customer Type",
            "fieldtype": "Select",
            "options": "\nWalk-in\nArchitect Referral\nBuilder\nContractor\nOnline\nRepeat",
            "insert_after": "customer_group",
        },
        {
            "fieldname": "lead_source_kvh",
            "label": "Lead Source",
            "fieldtype": "Data",
            "insert_after": "customer_type_kvh",
        },
        {
            "fieldname": "assigned_cre",
            "label": "Assigned CRE",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "lead_source_kvh",
        },
        {
            "fieldname": "architect",
            "label": "Architect",
            "fieldtype": "Data",
            "insert_after": "assigned_cre",
        },
        {
            "fieldname": "builder",
            "label": "Builder",
            "fieldtype": "Data",
            "insert_after": "architect",
        },
        {
            "fieldname": "contractor",
            "label": "Contractor",
            "fieldtype": "Data",
            "insert_after": "builder",
        },
    ]
    _create_fields("Customer", fields)


def create_supplier_fields():
    """Custom fields for Supplier to match KVH vendor data."""
    fields = [
        {
            "fieldname": "on_time_pct",
            "label": "On-Time Delivery %",
            "fieldtype": "Percent",
            "insert_after": "supplier_name",
            "read_only": 1,
        },
        {
            "fieldname": "opening_balance",
            "label": "Opening Balance",
            "fieldtype": "Currency",
            "insert_after": "on_time_pct",
        },
    ]
    _create_fields("Supplier", fields)


def create_purchase_order_fields():
    """Custom fields for Purchase Order to match KVH PO data."""
    fields = [
        {
            "fieldname": "kvh_po_status",
            "label": "KVH PO Status",
            "fieldtype": "Select",
            "options": "\nDraft\nConfirmed\nMRN_Generated\nReceived\nCancelled",
            "default": "Draft",
            "insert_after": "status",
            "in_list_view": 1,
        },
        {
            "fieldname": "kvh_mrn_number",
            "label": "MRN Number",
            "fieldtype": "Data",
            "insert_after": "kvh_po_status",
            "read_only": 1,
        },
        {
            "fieldname": "kvh_payment_status",
            "label": "Payment Status",
            "fieldtype": "Select",
            "options": "\nPending\nPartial\nPaid",
            "default": "Pending",
            "insert_after": "kvh_mrn_number",
            "read_only": 1,
        },
        {
            "fieldname": "inwarded_at",
            "label": "Inwarded At",
            "fieldtype": "Datetime",
            "insert_after": "kvh_payment_status",
            "read_only": 1,
        },
    ]
    _create_fields("Purchase Order", fields)


def create_item_fields():
    """Custom fields for Item (Inventory) to match KVH inventory_items data."""
    fields = [
        {
            "fieldname": "kvh_category",
            "label": "KVH Category",
            "fieldtype": "Select",
            "options": "\nRaw_Material\nConsumables\nMachinery\nSpares",
            "insert_after": "item_group",
        },
        {
            "fieldname": "min_stock_level",
            "label": "Minimum Stock Level",
            "fieldtype": "Float",
            "insert_after": "kvh_category",
        },
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "insert_after": "min_stock_level",
        },
    ]
    _create_fields("Item", fields)


def _create_fields(doctype, fields):
    """Helper to create custom fields if they don't exist."""
    for field in fields:
        fieldname = field["fieldname"]
        if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            cf = frappe.new_doc("Custom Field")
            cf.dt = doctype
            cf.module = "KVH Ops"
            for k, v in field.items():
                cf.set(k, v)
            cf.insert(ignore_permissions=True)
