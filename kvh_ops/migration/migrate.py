#!/usr/bin/env python3
"""
KVH Operations Data Migration Script
=====================================
Migrates data from the Lovable Supabase PostgreSQL database to ERPNext/Frappe.

Usage:
    bench --site your-site.com execute kvh_ops.migration.migrate --kwargs '{"supabase_url": "...", "supabase_key": "..."}'

Or run individual phases:
    bench --site your-site.com execute kvh_ops.migration.migrate_phase --kwargs '{"phase": "users", ...}'

Prerequisites:
    pip install supabase psycopg2-binary
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate
import json


# ============================================================
# PHASE 1: USERS & ROLES
# ============================================================

def migrate_users(profiles_data: list) -> dict:
    """
    Migrate user profiles from Supabase to Frappe Users.

    Lovable source: public.profiles
    ERPNext target: User + Has Role

    Role mapping:
        Admin           → KVH Admin + System Manager
        CRE             → KVH CRE
        Sales_Head      → KVH Sales Head
        BDM             → KVH BDM
        Design_Team     → KVH Design Team
        Production_Head → KVH Production Head
        Production_Manager → KVH Production Manager
        Factory_Supervisor → KVH Factory Supervisor
        Store_Keeper    → KVH Store Keeper
        Purchase_Officer → KVH Purchase Officer
        Marketing_Head  → KVH Marketing Head
        Marketing_Member → KVH Marketing Member
        Operation_Manager → KVH Operation Manager
    """
    role_map = {
        "Admin": ["KVH Admin", "System Manager"],
        "CRE": ["KVH CRE"],
        "Sales_Head": ["KVH Sales Head"],
        "BDM": ["KVH BDM"],
        "Design_Team": ["KVH Design Team"],
        "Production_Head": ["KVH Production Head"],
        "Production_Manager": ["KVH Production Manager"],
        "Factory_Supervisor": ["KVH Factory Supervisor"],
        "Store_Keeper": ["KVH Store Keeper"],
        "Purchase_Officer": ["KVH Purchase Officer"],
        "Marketing_Head": ["KVH Marketing Head"],
        "Marketing_Member": ["KVH Marketing Member"],
        "Operation_Manager": ["KVH Operation Manager"],
    }

    migrated = 0
    skipped = 0
    errors = []

    for profile in profiles_data:
        email = profile.get("email", "")
        if not email:
            errors.append(f"Profile {profile.get('id')} has no email — skipped")
            skipped += 1
            continue

        try:
            if frappe.db.exists("User", email):
                user = frappe.get_doc("User", email)
            else:
                user = frappe.new_doc("User")
                user.email = email
                user.first_name = profile.get("full_name", email.split("@")[0]).split()[0]
                last_parts = profile.get("full_name", "").split()
                user.last_name = " ".join(last_parts[1:]) if len(last_parts) > 1 else ""
                user.send_welcome_email = 0

            user.enabled = 1 if profile.get("active", True) else 0

            # Store KVH-specific metadata in user description
            branch = profile.get("branch", "")
            if branch:
                user.location = branch

            user.save(ignore_permissions=True)

            # Assign roles
            role = profile.get("role", "")
            roles_to_assign = role_map.get(role, [])

            # Also handle multi-role (roles[] array from Lovable)
            extra_roles = profile.get("roles", [])
            for extra_role in extra_roles:
                mapped = role_map.get(extra_role, [])
                roles_to_assign.extend(mapped)

            roles_to_assign = list(set(roles_to_assign))  # deduplicate

            for role_name in roles_to_assign:
                if not frappe.db.exists("Has Role", {"parent": email, "role": role_name}):
                    user.append("roles", {"role": role_name})

            user.save(ignore_permissions=True)
            migrated += 1

        except Exception as e:
            errors.append(f"User {email}: {e}")

    return {"migrated": migrated, "skipped": skipped, "errors": errors}


# ============================================================
# PHASE 2: CLIENTS / CUSTOMERS
# ============================================================

def migrate_clients(clients_data: list) -> dict:
    """
    Migrate clients from Lovable to ERPNext Customers.

    Lovable source: public.clients
    ERPNext target: Customer
    """
    migrated = 0
    errors = []

    for client in clients_data:
        try:
            customer_name = client.get("name", "")
            if not customer_name:
                continue

            if not frappe.db.exists("Customer", {"customer_name": customer_name}):
                doc = frappe.new_doc("Customer")
                doc.customer_name = customer_name
                doc.customer_type = "Individual"
                doc.customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups"
                doc.territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
                doc.mobile_no = client.get("phone", "")
                doc.email_id = client.get("email", "")

                # Custom fields
                doc.set("customer_number_kvh", client.get("client_number", ""))
                doc.set("district", client.get("district", ""))

                doc.insert(ignore_permissions=True)
                migrated += 1

        except Exception as e:
            errors.append(f"Client {client.get('name')}: {e}")

    return {"migrated": migrated, "errors": errors}


# ============================================================
# PHASE 3: VENDORS / SUPPLIERS
# ============================================================

def migrate_vendors(vendors_data: list) -> dict:
    """
    Migrate vendors from Lovable to ERPNext Suppliers.

    Lovable source: public.vendors
    ERPNext target: Supplier
    """
    migrated = 0
    errors = []

    for vendor in vendors_data:
        try:
            name = vendor.get("name", "")
            if not name:
                continue

            if not frappe.db.exists("Supplier", {"supplier_name": name}):
                doc = frappe.new_doc("Supplier")
                doc.supplier_name = name
                doc.supplier_group = "All Supplier Groups"
                doc.supplier_type = "Company"
                doc.gst_category = "Registered Regular"
                doc.gstin = vendor.get("gst", "")

                # Contact info
                doc.mobile_no = vendor.get("phone", "")
                doc.email_id = vendor.get("email", "")

                # Address from jsonb
                address = vendor.get("address", {})
                if isinstance(address, str):
                    try:
                        address = json.loads(address)
                    except Exception:
                        address = {}

                # Custom fields
                doc.set("on_time_pct", vendor.get("on_time_pct", 0))
                doc.set("opening_balance", vendor.get("opening_balance", 0))

                doc.insert(ignore_permissions=True)

                # Create address if available
                if address:
                    _create_supplier_address(doc.name, address)

                migrated += 1

        except Exception as e:
            errors.append(f"Vendor {vendor.get('name')}: {e}")

    return {"migrated": migrated, "errors": errors}


def _create_supplier_address(supplier_name, address_dict):
    """Create a Frappe Address linked to a Supplier."""
    try:
        addr = frappe.new_doc("Address")
        addr.address_title = supplier_name
        addr.address_type = "Billing"
        addr.address_line1 = address_dict.get("line1", address_dict.get("street", ""))
        addr.city = address_dict.get("city", "")
        addr.state = address_dict.get("state", "")
        addr.pincode = address_dict.get("pin", address_dict.get("pincode", ""))
        addr.country = "India"
        addr.append("links", {"link_doctype": "Supplier", "link_name": supplier_name})
        addr.insert(ignore_permissions=True)
    except Exception:
        pass


# ============================================================
# PHASE 4: INVENTORY ITEMS
# ============================================================

def migrate_inventory_items(items_data: list) -> dict:
    """
    Migrate inventory items from Lovable to ERPNext Items.

    Lovable source: public.inventory_items
    ERPNext target: Item

    Category mapping:
        Raw_Material  → Raw Material (Item Group)
        Consumables   → Consumable
        Machinery     → Fixed Asset
        Spares        → Spare Parts
    """
    group_map = {
        "Raw_Material": "Raw Material",
        "Consumables": "Consumable",
        "Machinery": "Fixed Asset",
        "Spares": "Spare Parts",
    }

    migrated = 0
    errors = []

    for item in items_data:
        try:
            sku = item.get("sku", "")
            name = item.get("item_name", sku)
            if not sku or not name:
                continue

            if frappe.db.exists("Item", sku):
                continue

            category = item.get("category", "Raw_Material")
            item_group = group_map.get(category, "All Item Groups")

            # Ensure item group exists
            if not frappe.db.exists("Item Group", item_group):
                item_group = "All Item Groups"

            doc = frappe.new_doc("Item")
            doc.item_code = sku
            doc.item_name = name
            doc.item_group = item_group
            doc.stock_uom = item.get("unit_of_measurement", "Nos")
            doc.is_stock_item = 1
            doc.include_item_in_manufacturing = 0

            # Custom fields
            doc.set("kvh_category", category)
            doc.set("min_stock_level", item.get("min_stock_level", 0))
            doc.set("branch", item.get("branch", ""))

            doc.insert(ignore_permissions=True)
            migrated += 1

        except Exception as e:
            errors.append(f"Item {item.get('sku')}: {e}")

    return {"migrated": migrated, "errors": errors}


# ============================================================
# PHASE 5: SALES ORDERS
# ============================================================

def migrate_sales_orders(orders_data: list, order_items_data: list) -> dict:
    """
    Migrate sales orders and items from Lovable to ERPNext Sales Orders.

    Lovable source: public.orders + public.order_items
    ERPNext target: Sales Order + Sales Order Item + KVH Job Card
    """
    # Index order items by order_id
    items_by_order = {}
    for item in order_items_data:
        oid = item.get("order_id", "")
        if oid not in items_by_order:
            items_by_order[oid] = []
        items_by_order[oid].append(item)

    migrated = 0
    errors = []

    for order in orders_data:
        try:
            order_id = order.get("order_id", "")
            if not order_id:
                continue

            # Check if already migrated (use custom field or check name)
            if frappe.db.exists("Sales Order", {"customer_name": order.get("customer_name"),
                                                 "transaction_date": order.get("ordered_date")}):
                continue

            customer_name = order.get("customer_name", "")

            # Ensure customer exists
            if not frappe.db.exists("Customer", {"customer_name": customer_name}):
                frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_type": "Individual",
                    "customer_group": "All Customer Groups",
                    "territory": "All Territories",
                }).insert(ignore_permissions=True)

            so = frappe.new_doc("Sales Order")
            so.customer = frappe.db.get_value("Customer", {"customer_name": customer_name}, "name") or customer_name
            so.customer_name = customer_name
            so.transaction_date = order.get("ordered_date") or frappe.utils.today()
            so.delivery_date = order.get("committed_delivery_date") or frappe.utils.today()
            so.order_type = "Sales"

            # Custom fields
            so.set("committed_delivery_date", order.get("committed_delivery_date"))
            so.set("kvh_finish_type", order.get("finish_type", "Primer Finish"))
            so.set("include_installation", 1 if order.get("include_installation") else 0)
            so.set("branch", order.get("branch", ""))
            so.set("cancellation_reason", order.get("cancellation_reason", ""))

            # Map old status to new kvh_production_status
            old_status = order.get("status", "Payment Pending")
            so.set("kvh_production_status", old_status)

            # Add items
            order_items = items_by_order.get(order_id, [])
            for idx, item in enumerate(order_items):
                so.append("items", {
                    "item_code": "SERVICE",  # Generic service item; create in ERPNext
                    "item_name": item.get("product_description", "Product"),
                    "description": item.get("product_description", ""),
                    "qty": item.get("quantity", 1),
                    "rate": 0,  # Price to be updated manually
                    "delivery_date": order.get("committed_delivery_date") or frappe.utils.today(),
                    "sheet_spec": item.get("sheet_spec", ""),
                    "grill_spec": item.get("grill_spec", ""),
                    "design_status": item.get("design_status", "Pending"),
                    "factory_stage": item.get("factory_stage", "Pending"),
                })

            if not so.items:
                so.append("items", {
                    "item_code": "SERVICE",
                    "item_name": "General Service",
                    "qty": 1,
                    "rate": order.get("amount", 0) or 0,
                    "delivery_date": so.delivery_date,
                })

            so.insert(ignore_permissions=True)

            # Note: Don't auto-submit; let staff review and submit
            migrated += 1

        except Exception as e:
            errors.append(f"Order {order.get('order_id')}: {e}")

    return {"migrated": migrated, "errors": errors}


# ============================================================
# PHASE 6: FABRICATORS
# ============================================================

def migrate_fabricators(fabricators_data: list, rate_card_data: list) -> dict:
    """
    Migrate fabricators and rate cards.

    Lovable source: public.fabricators + public.fabricator_rate_card
    ERPNext target: KVH Fabricator + KVH Fabricator Rate Card
    """
    migrated_fab = 0
    migrated_rates = 0
    errors = []

    for fab in fabricators_data:
        name = fab.get("name", "")
        if not name:
            continue
        try:
            if not frappe.db.exists("KVH Fabricator", name):
                doc = frappe.new_doc("KVH Fabricator")
                doc.fabricator_name = name
                doc.active = 1 if fab.get("active", True) else 0
                doc.insert(ignore_permissions=True)
                migrated_fab += 1
        except Exception as e:
            errors.append(f"Fabricator {name}: {e}")

    for rate in rate_card_data:
        product_key = rate.get("product_key", "")
        if not product_key:
            continue
        try:
            if not frappe.db.exists("KVH Fabricator Rate Card", product_key):
                doc = frappe.new_doc("KVH Fabricator Rate Card")
                doc.product_key = product_key
                doc.display_name = rate.get("display_name", product_key)
                doc.rate = rate.get("rate", 0)
                doc.active = 1 if rate.get("active", True) else 0
                doc.insert(ignore_permissions=True)
                migrated_rates += 1
        except Exception as e:
            errors.append(f"Rate card {product_key}: {e}")

    return {"fabricators": migrated_fab, "rate_cards": migrated_rates, "errors": errors}


# ============================================================
# PHASE 7: LEADS
# ============================================================

def migrate_leads(leads_data: list) -> dict:
    """
    Migrate leads from Lovable to ERPNext CRM Leads.

    Lovable source: public.leads
    ERPNext target: CRM Lead (with custom fields)
    """
    migrated = 0
    errors = []

    for lead in leads_data:
        try:
            lead_name = lead.get("name", "")
            email = lead.get("email", "")
            phone = lead.get("phone", "")

            if not lead_name and not email and not phone:
                continue

            doc = frappe.new_doc("CRM Lead")
            doc.lead_name = lead_name or email or phone
            doc.mobile_no = phone
            doc.email_id = email
            doc.source = lead.get("source", "")
            doc.lead_stage = lead.get("stage_key", "New")
            doc.notes = lead.get("notes", "")
            doc.lead_owner = _map_user_by_id(lead.get("owner_id"))

            # Custom fields
            doc.set("lead_number", lead.get("lead_number", ""))
            doc.set("phone_norm", lead.get("phone_norm", ""))
            doc.set("is_duplicate", lead.get("is_duplicate", 0))
            doc.set("ai_summary", lead.get("ai_summary", ""))
            doc.set("place", lead.get("place", ""))
            doc.set("branch", lead.get("branch", ""))
            doc.set("last_contacted_at", lead.get("last_contacted_at"))
            doc.set("next_followup_at", lead.get("next_followup_at"))

            doc.insert(ignore_permissions=True)
            migrated += 1

        except Exception as e:
            errors.append(f"Lead {lead.get('id')}: {e}")

    return {"migrated": migrated, "errors": errors}


# ============================================================
# HELPERS
# ============================================================

def _map_user_by_id(user_id):
    """Map Supabase UUID to Frappe user email (if migrated)."""
    # During migration, you would build a uuid→email lookup dict
    # For now, return None to let ERPNext use the current user
    return None


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def run_full_migration(data: dict) -> dict:
    """
    Run the complete migration from Supabase data.

    Args:
        data: dict with keys: profiles, clients, vendors, inventory_items,
              orders, order_items, fabricators, rate_cards, leads

    Returns:
        dict with migration statistics for each phase
    """
    results = {}

    print("Phase 1: Migrating users...")
    results["users"] = migrate_users(data.get("profiles", []))

    print("Phase 2: Migrating clients/customers...")
    results["clients"] = migrate_clients(data.get("clients", []))

    print("Phase 3: Migrating vendors/suppliers...")
    results["vendors"] = migrate_vendors(data.get("vendors", []))

    print("Phase 4: Migrating inventory items...")
    results["items"] = migrate_inventory_items(data.get("inventory_items", []))

    print("Phase 5: Migrating fabricators...")
    results["fabricators"] = migrate_fabricators(
        data.get("fabricators", []),
        data.get("rate_cards", [])
    )

    print("Phase 6: Migrating leads...")
    results["leads"] = migrate_leads(data.get("leads", []))

    print("Phase 7: Migrating sales orders...")
    results["sales_orders"] = migrate_sales_orders(
        data.get("orders", []),
        data.get("order_items", [])
    )

    frappe.db.commit()

    print("\n=== MIGRATION COMPLETE ===")
    for phase, result in results.items():
        print(f"{phase}: {result}")

    return results
