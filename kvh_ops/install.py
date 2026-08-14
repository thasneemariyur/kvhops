import frappe
from frappe import _


def after_install():
    """Run after app installation to set up initial data."""
    create_roles()
    create_kvh_naming_series()
    create_feature_flags()
    create_default_stages()
    create_default_dropdown_options()
    frappe.db.commit()
    frappe.msgprint(_("KVH Operations app installed successfully."))


def create_roles():
    """Create KVH-specific roles."""
    roles = [
        ("KVH Admin", "Full administrative access to KVH Operations"),
        ("KVH CRE", "Customer Relationship Executive - creates orders, manages own clients"),
        ("KVH Sales Head", "Sales Head - manages all CREs and orders"),
        ("KVH BDM", "Business Development Manager - sales management"),
        ("KVH Design Team", "Design team member - manages design stages"),
        ("KVH Production Head", "Production Head - full factory management"),
        ("KVH Production Manager", "Production Manager - day-to-day factory ops"),
        ("KVH Factory Supervisor", "Factory Supervisor - manages fabricators and reworks"),
        ("KVH Store Keeper", "Store Keeper - inventory and materials management"),
        ("KVH Purchase Officer", "Purchase Officer - procurement management"),
        ("KVH Marketing Head", "Marketing Head - full marketing module access"),
        ("KVH Marketing Member", "Marketing team contributor"),
        ("KVH Operation Manager", "Cross-functional operations visibility"),
    ]

    for role_name, description in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.description = description
            role.insert(ignore_permissions=True)


def create_kvh_naming_series():
    """Configure naming series for KVH documents."""
    naming_series_config = {
        "Sales Order": "KVH/OR/.FY./.####",
        "Purchase Order": "KVH/PO/.FY./.####",
        "Material Request": "KVH/MRN/.FY./.####",
        "Issue": "KVH/TKT/.FY./.####",
    }

    for doctype, series in naming_series_config.items():
        try:
            dt_meta = frappe.get_meta(doctype)
            if dt_meta:
                existing = frappe.db.get_value("DocType", doctype, "autoname") or ""
                # Don't overwrite if already has KVH series
                if "KVH" not in existing:
                    frappe.db.set_value("DocType", doctype, "autoname", series)
        except Exception:
            pass


def create_feature_flags():
    """Create default feature flags."""
    flags = [
        ("incentives_page", "Incentives Page", "Show the Incentives module in navigation", 1),
        ("rework_flow", "Rework Flow", "Enable Send to Rework actions across factory and design", 1),
        ("cnc_stage", "CNC Stage", "Include CNC in the factory pipeline", 1),
        ("installation_module", "Installation Module", "Enable the Installation route and assignments", 1),
    ]

    for key, label, description, enabled in flags:
        if not frappe.db.exists("KVH Feature Flag", key):
            doc = frappe.new_doc("KVH Feature Flag")
            doc.name = key
            doc.label = label
            doc.description = description
            doc.enabled = enabled
            doc.insert(ignore_permissions=True)


def create_default_stages():
    """Create default CRM lead stages."""
    if not frappe.db.table_exists("CRM Stage"):
        return

    stages = [
        ("new", "New", "#3b82f6", 10, 0, 0),
        ("contacted", "Contacted", "#06b6d4", 20, 0, 0),
        ("qualified", "Qualified", "#8b5cf6", 30, 0, 0),
        ("proposal", "Proposal Sent", "#f59e0b", 40, 0, 0),
        ("negotiation", "Negotiation", "#ec4899", 50, 0, 0),
        ("won", "Won", "#10b981", 60, 1, 1),
        ("lost", "Lost", "#ef4444", 70, 1, 0),
    ]

    for key, label, color, sort_order, is_terminal, is_won in stages:
        try:
            if not frappe.db.exists("CRM Stage", {"stage_name": label}):
                stage = frappe.new_doc("CRM Stage")
                stage.stage_name = label
                stage.insert(ignore_permissions=True)
        except Exception:
            pass


def create_default_dropdown_options():
    """Create default rework reasons and other options."""
    rework_reasons = [
        "Wrong measurement",
        "Surface defect",
        "Damaged in transit",
        "Customer change",
        "Quality rejection",
    ]

    for reason in rework_reasons:
        if not frappe.db.exists("KVH Rework Reason", reason):
            try:
                doc = frappe.new_doc("KVH Rework Reason")
                doc.reason = reason
                doc.insert(ignore_permissions=True)
            except Exception:
                pass
