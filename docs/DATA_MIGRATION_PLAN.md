# KVH Operations — Data Migration Plan

## Overview

This document details the complete, sequenced plan for migrating live data from the existing KVH Supabase PostgreSQL database to the new ERPNext system.

> [!IMPORTANT]
> Perform a full Supabase database backup before beginning migration. Run migration on a **staging site first** and verify all record counts and spot-checks before executing on production.

---

## Migration Principles

1. **Zero data loss** — Every record must be accounted for
2. **Phased execution** — Migrate in dependency order (roles → customers → orders)
3. **Idempotent scripts** — Running twice must not create duplicates
4. **Parallel systems** — Keep Lovable live until ERPNext is fully verified
5. **Rollback plan** — Keep Supabase live; ERPNext is additive until cutover

---

## Pre-Migration Checklist

- [ ] ERPNext site fully installed and configured
- [ ] All custom DocTypes installed (`bench migrate`)
- [ ] All custom fields created (`create_all_custom_fields()`)
- [ ] Naming series configured in ERPNext
- [ ] Branches created in ERPNext matching Lovable branches
- [ ] Warehouses created
- [ ] Item Groups created (Raw Material, Consumable, Fixed Asset, Spare Parts)
- [ ] "SERVICE" generic item created for order migration
- [ ] Frappe roles verified (13 KVH roles exist)
- [ ] Supabase read-only service key obtained
- [ ] Migration environment variables set

---

## Migration Phases

### Phase 0: Reference Data (No Dependencies)

**Estimated Time:** 15 minutes

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Branches | `profiles.branch` (distinct) | Branch | Create unique branch names |
| Lead stages | `lead_stages` | CRM Stage | Key + Label mapping |
| Fabricators | `fabricators` | KVH Fabricator | Active/inactive flag |
| Fabricator rate cards | `fabricator_rate_card` | KVH Fabricator Rate Card | product_key normalized |
| Feature flags | `feature_flags` | KVH Feature Flag | All 4 flags with current state |
| Dropdown options | `dropdown_options` | Select field options | Via Frappe Customize Form |

**Script:**
```bash
bench --site kvh.yourdomain.com execute kvh_ops.migration.migrate.migrate_fabricators \
  --kwargs '{"fabricators_data": [...], "rate_card_data": [...]}'
```

---

### Phase 1: Users & Roles

**Estimated Time:** 30 minutes  
**Dependency:** Phase 0 (branches)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| User accounts | `auth.users` | User | Email as username |
| User profiles | `public.profiles` | User (extended) | full_name, branch, active |
| Role assignments | `profiles.role` + `profiles.roles[]` | Has Role | Multi-role mapped |

**Validation Checks:**
```sql
-- Supabase: count active profiles
SELECT COUNT(*) FROM public.profiles WHERE active = true;
-- ERPNext: count enabled users with KVH roles
SELECT COUNT(DISTINCT parent) FROM `tabHas Role` WHERE role LIKE 'KVH%';
```

**Post-Migration Actions:**
- Send password reset emails to all migrated users
- Ask users to verify their profile data

---

### Phase 2: Customers & Suppliers

**Estimated Time:** 20 minutes  
**Dependency:** Phase 1 (users for assigned_cre)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Clients | `public.clients` | Customer | customer_number_kvh custom field |
| SM Customers | `public.sm_customers` | Customer (merge/update) | Merge if email/phone matches |
| Vendors | `public.vendors` | Supplier | GST, address, on_time_pct |
| Vendor addresses | `public.vendors.address` (jsonb) | Address | Linked to Supplier |

**Validation Checks:**
```sql
-- Supabase counts
SELECT COUNT(*) FROM public.clients;
SELECT COUNT(*) FROM public.vendors WHERE active = true;
-- ERPNext counts
SELECT COUNT(*) FROM `tabCustomer`;
SELECT COUNT(*) FROM `tabSupplier`;
```

---

### Phase 3: Inventory

**Estimated Time:** 30 minutes  
**Dependency:** Phase 0 (item groups), Phase 2 (warehouses)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Inventory items | `public.inventory_items` | Item | SKU as item_code |
| Opening stock | `inventory_items.current_stock` | Stock Reconciliation | Post as of migration date |
| Machinery | `public.machinery_register` | Asset | Active/Under_Repair/Retired |
| Machinery repairs | `public.machinery_repairs` | Asset Maintenance Log | Historical records |

**Opening Stock Process:**
1. Export all items with `current_stock` from Supabase
2. Create one Stock Reconciliation per branch/warehouse
3. Submit Stock Reconciliation to set opening stock
4. Verify Item Ledger matches Supabase `material_transactions` net total

---

### Phase 4: Leads

**Estimated Time:** 45 minutes  
**Dependency:** Phase 1 (users as lead owners)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Leads | `public.leads` | CRM Lead | All custom fields |
| Lead calls | `public.lead_calls` | CRM Call Log | Linked to CRM Lead |
| Lead follow-ups | `public.lead_followups` | CRM Appointment | Due date mapping |
| Lead activities | `public.lead_activities` | CRM Note | Stage/owner change events |
| Lead images | `public.lead_images` | File | Download from Supabase Storage, attach to Lead |
| Lead stages | `public.lead_stages` | CRM Stage | Custom stages with colors |

**Duplicate Leads:**
- Leads with `is_duplicate=true` are migrated with the flag set
- `merged_into` links are preserved as CRM Lead links
- Duplicate leads are marked but not deleted

**Validation:**
```sql
-- Supabase
SELECT COUNT(*) FROM public.leads;
SELECT COUNT(*) FROM public.leads WHERE is_duplicate = true;
-- ERPNext
SELECT COUNT(*) FROM `tabCRM Lead`;
SELECT COUNT(*) FROM `tabCRM Lead` WHERE is_duplicate = 1;
```

---

### Phase 5: Sales Orders & Production

**Estimated Time:** 2–4 hours (depending on order count)  
**Dependency:** Phase 1 (users), Phase 2 (customers), Phase 3 (items)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Orders | `public.orders` | Sales Order | Draft state initially |
| Order items | `public.order_items` | Sales Order Item | Custom fields: design_status, factory_stage |
| Job Cards | `public.order_items` | KVH Job Card | Auto-created from order items |
| Stage events | `public.order_item_stage_events` | KVH Stage Event | Historical audit trail |
| Reworks | `public.reworks` | KVH Rework | Linked to Job Card |
| Design logs | `public.design_logs` | KVH Design Log | Per-designer daily logs |
| Edit requests | `public.order_edit_requests` | KVH Order Edit Request | Historical requests |

**Order Migration Notes:**
- Orders migrate as **Draft** first — do not auto-submit
- Staff reviews and submits orders in batches
- Cancelled orders migrate with `kvh_production_status = "Cancelled"` and cancellation_reason
- Payment amounts recorded as custom fields (not as ERPNext Payment Entries initially)
- Delivery notes created separately for delivered orders

**Post-Migration Job Card Creation:**
```python
# For each migrated Sales Order, create Job Cards manually if not auto-created
bench --site kvh.yourdomain.com execute kvh_ops.migration.migrate_job_cards
```

---

### Phase 6: Procurement

**Estimated Time:** 1 hour  
**Dependency:** Phase 2 (suppliers), Phase 3 (items)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Purchase requisitions | `public.purchase_requisitions` | Material Request | Status mapping |
| PR items | `public.purchase_requisition_items` | Material Request Item | |
| RFQs | `public.rfqs` | Request for Quotation | |
| POs | `public.purchase_orders` | Purchase Order | kvh_po_status, mrn_number |
| PO items | `public.purchase_order_items` | Purchase Order Item | |
| PO payments | `public.po_payments` | Payment Entry | reference_name = PO name |
| Supplier invoices | `public.supplier_invoices` | Purchase Invoice | GST components |
| Debit notes | `public.debit_notes` | Purchase Invoice (Return) | |
| Material transfers | `public.material_transfers` | Stock Entry (Transfer) | |
| Stock audits | `public.stock_audits` | Stock Reconciliation | Historical |

---

### Phase 7: Fabricator Payouts

**Estimated Time:** 30 minutes  
**Dependency:** Phase 0 (fabricators, rate cards), Phase 5 (job cards)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Payout runs | `public.fabricator_payout_runs` | KVH Fabricator Payout | Status preserved |
| Payout lines | `public.fabricator_payout_lines` | KVH Fabricator Payout Item | amount = qty × rate |

**Notes:**
- Paid runs migrate as **Paid** status (read-only historical)
- Draft runs migrate as **Draft** — staff can continue editing
- Approved runs migrate as **Approved**

---

### Phase 8: Marketing

**Estimated Time:** 45 minutes  
**Dependency:** Phase 2 (clients)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Marketing clients | `public.marketing_clients` | KVH Marketing Client | |
| Campaigns | `public.marketing_campaigns` | KVH Marketing Campaign | campaign_code → name |
| Content items | `public.marketing_content_items` | KVH Marketing Content Item | Child of Campaign |
| Paid ads | `public.marketing_paid_ads` | KVH Marketing Ad Item | Child of Campaign |
| Brand assets | `public.marketing_brand_assets` | KVH Brand Asset | Files downloaded |
| Subscriptions | `public.marketing_subscriptions` | KVH Marketing Subscription | Active ones migrated |
| Budget entries | `public.marketing_budget_entries` | KVH Marketing Budget Entry | |
| Marketing invoices | `public.marketing_invoices` | KVH Marketing Invoice | Token regenerated |
| Invoice items | `public.marketing_invoice_items` | KVH Marketing Invoice Item | Child table |
| Invoice payments | `public.marketing_invoice_payments` | KVH Marketing Invoice Payment | Child table |
| MIS snapshots | `public.marketing_mis_snapshots` | KVH Marketing MIS Snapshot | Final snapshots only |

**Token Migration Note:**
- Public invoice tokens are regenerated in ERPNext
- Share new public URLs with clients after migration

---

### Phase 9: Sales Management

**Estimated Time:** 30 minutes  
**Dependency:** Phase 1 (users), Phase 2 (customers)

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Sales targets | `public.sm_targets` | KVH Sales Target | Historical + current |
| Weekly reports | `public.sm_weekly_reports` | KVH Weekly Report | auto_snapshot as JSON |
| Customer feedback | `public.sm_feedback` | KVH Customer Feedback | Rating, category |
| Incentive rules | `public.incentive_rules` | KVH Incentive Rule | Tiers → child table |

---

### Phase 10: Service Desk

**Estimated Time:** 20 minutes  
**Dependency:** Phase 1, Phase 2

| Data | Supabase Table | ERPNext DocType | Notes |
|---|---|---|---|
| Service tickets | `public.service_tickets` | Issue | ticket_number preserved |

---

## Data Export Script (Supabase)

```javascript
// Run in Supabase Edge Function or local script
const { createClient } = require('@supabase/supabase-js')
const fs = require('fs')

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY)

async function exportAll() {
  const tables = [
    'profiles', 'clients', 'vendors', 'inventory_items',
    'fabricators', 'fabricator_rate_card', 'feature_flags',
    'leads', 'lead_stages', 'lead_calls', 'lead_followups',
    'orders', 'order_items', 'order_item_stage_events', 'reworks',
    'purchase_orders', 'purchase_order_items', 'po_payments',
    'supplier_invoices', 'material_transfers',
    'fabricator_payout_runs', 'fabricator_payout_lines',
    'marketing_clients', 'marketing_campaigns', 'marketing_invoices',
    'marketing_invoice_items', 'marketing_invoice_payments',
    'marketing_subscriptions', 'sm_targets', 'sm_feedback',
    'incentive_rules', 'service_tickets',
  ]
  
  const data = {}
  for (const table of tables) {
    const { data: rows, error } = await supabase
      .from(table)
      .select('*')
      .order('created_at', { ascending: true })
    
    if (error) console.error(`Error exporting ${table}:`, error)
    else {
      data[table] = rows
      console.log(`Exported ${rows.length} rows from ${table}`)
    }
  }
  
  fs.writeFileSync('kvh_export.json', JSON.stringify(data, null, 2))
  console.log('Export complete: kvh_export.json')
}
exportAll()
```

---

## Cutover Plan

### T-7 Days Before Cutover
- [ ] Migration fully tested on staging
- [ ] All feature parity tests passing (see FEATURE_PARITY_TESTING.md)
- [ ] Staff trained on ERPNext interface
- [ ] Go/No-go decision made with management

### T-1 Day
- [ ] Final data sync (run migration again on latest Supabase snapshot)
- [ ] Lock Lovable: set to read-only mode (disable form submissions)
- [ ] Communicate cutover window to all users

### Cutover Day (suggested: Friday evening)
1. Take final Supabase export at cutover time
2. Run full migration on production ERPNext
3. Verify all record counts
4. Enable ERPNext for all users
5. Keep Lovable accessible in read-only mode for 2 weeks (reference)

### T+7 Days
- [ ] Verify all workflows operating normally
- [ ] All staff comfortable with ERPNext
- [ ] No critical bugs open

### T+30 Days
- [ ] Decommission Lovable/Supabase
- [ ] Final Supabase data backup archived
- [ ] Project closed

---

## Rollback Plan

If critical issues are found during cutover:
1. Re-enable Lovable for all users (it was never disabled, just made read-only)
2. Communicate delay to users
3. Fix ERPNext issues
4. Re-run migration with fixes
5. Retry cutover

> [!CAUTION]
> Do NOT delete Supabase data until at least 30 days after successful cutover and all data is verified in ERPNext.
