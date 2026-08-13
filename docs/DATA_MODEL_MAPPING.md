# KVH Operations — Data Model Mapping

## Database Type Mappings

| PostgreSQL Type | Frappe Field Type | Notes |
|---|---|---|
| `uuid` | `Link` (to parent) or `Data` | Use Data for migrated IDs, Link for relationships |
| `text` | `Data` or `Small Text` | Data for <140 chars, Small Text for longer |
| `text NOT NULL DEFAULT ''` | `Data` with default `""` | Set mandatory=0, default="" |
| `numeric` / `decimal` | `Currency` or `Float` | Currency for money, Float for quantities |
| `integer` / `int` | `Int` | Direct mapping |
| `boolean` | `Check` | Default 0/1 |
| `timestamptz` | `Datetime` | ERPNext stores in UTC |
| `date` | `Date` | Direct mapping |
| `jsonb` | `JSON` or child table | Simple jsonb → JSON field; structured jsonb → child table |
| `text[]` (array) | `Table MultiSelect` or `JSON` | Use child table for managed lists |
| `ENUM type` | `Select` field | Options become the Select options list |
| `uuid PRIMARY KEY` | DocType name (auto `name` field) | Frappe uses `name` as PK (string) |

## Enum → Select Field Mappings

### `order_status` → `kvh_production_status`
```
Payment Pending
Pending Design
In Design
Pending CNC
In Fabrication
Ready for Delivery
Ready for Installation
Delivered
Cancelled
```

### `factory_stage` → KVH Job Card `factory_stage`
```
Pending
CNC
Fabrication
Surface Finishing
Primer Coating
Powder Coating
PU Foam Filling
Accessories
Packing
Installation
Ready
Dispatched
```

### `design_status` → KVH Job Card `design_status`
```
Pending
In Progress
Hold
Completed
```

### `payment_status` → Sales Order `kvh_payment_status`
```
Payment Pending
Advance Received
Fully Paid
```

### `po_status` → Purchase Order `kvh_po_status`
```
Draft
Confirmed
MRN_Generated
Received
Cancelled
```

### `edit_request_status` → KVH Order Edit Request `status`
```
Pending
Approved
Rejected
Used
Expired
```

### `mkt_invoice_status` → KVH Marketing Invoice `status`
```
Draft
Sent
Partially Paid
Paid
Cancelled
```

### `mkt_invoice_item_kind` → KVH Marketing Invoice Item `kind`
```
Retainer
Ad Spend
Subscription
Service
Other
```

### `mkt_content_status` → KVH Marketing Content `content_status`
```
Idea
Drafting
Designing
Internal Review
Client Review
Approved
Scheduled
Published
Cancelled
```

### `mkt_campaign_status` → KVH Marketing Campaign `status`
```
Draft
Internal Review
Client Approval
Approved
Live
Completed
Cancelled
```

### `mkt_mis_status` → KVH Marketing MIS Snapshot `status`
```
Draft
Final
```

### `inventory_category` → Item `kvh_category`
```
Raw_Material
Consumables
Machinery
Spares
```

### `app_role` → Frappe Roles
```
Admin              → KVH Admin
CRE                → KVH CRE
Sales_Head         → KVH Sales Head
BDM                → KVH BDM
Design_Team        → KVH Design Team
Production_Head    → KVH Production Head
Production_Manager → KVH Production Manager
Factory_Supervisor → KVH Factory Supervisor
Store_Keeper       → KVH Store Keeper
Purchase_Officer   → KVH Purchase Officer
Marketing_Head     → KVH Marketing Head
Marketing_Member   → KVH Marketing Member
Operation_Manager  → KVH Operation Manager
```

---

## Table-by-Table Mapping

### Core

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.profiles` | User | `id`→name(email), `full_name`→full_name, `role`→Has Role, `branch`→location, `active`→enabled |
| `auth.users` | User | `email`→name, password reset via Frappe |
| `public.orders` | Sales Order | `order_id`→name, `customer_name`→customer_name, `sales_person_id`→owner, `amount`→grand_total, `ordered_date`→transaction_date, `committed_delivery_date`→custom field, `status`→kvh_production_status, `finish_type`→kvh_finish_type, `include_installation`→include_installation, `branch`→branch |
| `public.order_items` | Sales Order Item + KVH Job Card | `item_id`→name(auto), `order_id`→sales_order/parent, `product_description`→item_name/description, `quantity`→qty, `design_status`→design_status(custom), `factory_stage`→factory_stage(custom), `designer_assigned_to`→designer_assigned_to(custom), `fabricator_name`→fabricator_name_text(custom) |
| `public.order_item_stage_events` | KVH Stage Event | `item_id`→job_card, `order_id`→sales_order, `stage`→stage, `event_kind`→event_kind, `actor_id`→actor, `assignee_id`→assignee |
| `public.reworks` | KVH Rework | `order_id`→sales_order, `item_id`→job_card, `reason`→reason, `stage`→stage, `status`→status, `supervisor_id`→supervisor |

### Lead Management

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.lead_stages` | CRM Stage | `key`→name, `label`→stage_name |
| `public.leads` | CRM Lead | `id`→name(auto), `lead_number`→lead_number(custom), `name`→lead_name, `phone`→mobile_no, `phone_norm`→phone_norm(custom), `email`→email_id, `source`→source, `stage_key`→lead_stage, `owner_id`→lead_owner, `notes`→notes, `is_duplicate`→is_duplicate(custom), `merged_into_id`→merged_into(custom), `ai_summary`→ai_summary(custom), `place`→place(custom), `branch`→branch(custom), `last_contacted_at`→last_contacted_at(custom), `next_followup_at`→next_followup_at(custom) |
| `public.lead_calls` | CRM Call Log | `lead_id`→reference_docname, `direction`→type, `outcome`→outcome, `duration_sec`→duration, `notes`→note, `called_by`→added_by |
| `public.lead_followups` | CRM Appointment | `lead_id`→lead, `due_at`→scheduled_time, `note`→notes, `assignee_id`→assigned_to |
| `public.lead_activities` | CRM Note | `lead_id`→reference_docname, `activity_type`→note type, `body`→note |
| `public.lead_images` | File | `lead_id`→attached_to_name, file_url→file_url |

### Procurement

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.vendors` | Supplier | `id`→name(auto), `name`→supplier_name, `gst`→gstin, `email`→email_id, `phone`→mobile_no, `address`→Address (separate), `on_time_pct`→on_time_pct(custom), `opening_balance`→opening_balance(custom) |
| `public.purchase_requisitions` | Material Request | `id`→name(auto), `department`→department, `requester_id`→requested_by, `needed_by`→schedule_date, `status`→status |
| `public.purchase_requisition_items` | Material Request Item | `item_name`→item_name, `quantity`→qty, `unit`→uom, `notes`→description |
| `public.rfqs` | Request for Quotation | `id`→name(auto), `status`→status |
| `public.rfq_vendors` | RFQ Supplier | `vendor_id`→supplier, `rfq_id`→parent |
| `public.rfq_quotations` | Supplier Quotation | linked via RFQ |
| `public.purchase_orders` | Purchase Order | `id`→name(auto), `po_number`→name override, `vendor_id`→supplier, `vendor_name`→supplier_name, `status`→kvh_po_status(custom), `mrn_number`→kvh_mrn_number(custom), `payment_status`→kvh_payment_status(custom) |
| `public.purchase_order_items` | Purchase Order Item | `item_id`→item_code, `quantity`→qty, `unit_price`→rate |
| `public.po_payments` | Payment Entry | `po_id`→reference_name, `amount`→paid_amount, `paid_on`→posting_date, `method`→mode_of_payment |
| `public.supplier_invoices` | Purchase Invoice | `invoice_number`→bill_no, `vendor_id`→supplier, `po_id`→purchase_order, `invoice_date`→bill_date, subtotals and tax → standard ERPNext tax fields |
| `public.material_transfers` | Stock Entry (Transfer) | `from_location`→from_warehouse, `to_location`→to_warehouse, `items`→Stock Entry Detail |
| `public.inventory_items` | Item | `sku`→item_code, `item_name`→item_name, `category`→kvh_category(custom)/item_group, `unit_of_measurement`→stock_uom, `min_stock_level`→min_stock_level(custom), `branch`→branch(custom) |
| `public.material_transactions` | Stock Ledger Entry (auto) | Created automatically via Stock Entry submission |
| `public.stock_audits` | Stock Reconciliation | `branch`→company, `audit_date`→posting_date, `status`→status |
| `public.stock_audit_lines` | Stock Reconciliation Item | `item_id`→item_code, `system_qty`→current_qty, `counted_qty`→qty |
| `public.machinery_register` | Asset | `machine_name`→asset_name, `status`→status, `purchased_on`→purchase_date |
| `public.machinery_repairs` | Asset Maintenance Log | `machine_id`→asset, `issue_description`→description, `repair_cost`→repair_cost |

### Fabricators

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.fabricators` | KVH Fabricator | `name`→fabricator_name, `active`→active |
| `public.fabricator_rate_card` | KVH Fabricator Rate Card | `product_key`→product_key, `display_name`→display_name, `rate`→rate, `active`→active |
| `public.fabricator_payout_runs` | KVH Fabricator Payout | `run_number`→run_number, `fabricator_id`→fabricator, `period_start`→period_start, `period_end`→period_end, `mode`→mode, `status`→status, `total_items`→total_items, `total_qty`→total_qty, `total_amount`→total_amount, `approved_by`→approved_by, `paid_at`→paid_at, `paid_reference`→paid_reference |
| `public.fabricator_payout_lines` | KVH Fabricator Payout Item | `item_id`→job_card, `order_id`→sales_order, `product_description`→product_description, `product_key`→product_key, `quantity`→quantity, `rate`→rate, `amount`→amount, `completed_at`→completed_at, `rate_override`→rate_override, `note`→note |

### Marketing

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.marketing_clients` | KVH Marketing Client | `name`→client_name, `contact`→contact, `email`→email, `monthly_retainer`→monthly_retainer, `active`→active |
| `public.marketing_campaigns` | KVH Marketing Campaign | `campaign_code`→name, `name`→campaign_name, `client_id`→client, `sub_team`→sub_team, `status`→status, `start_date`→start_date, `end_date`→end_date, `budget_allocated`→budget_allocated, `target_leads`→target_leads, `platforms`→platforms(JSON), `owner_id`→owner |
| `public.marketing_content_items` | KVH Marketing Content | `campaign_id`→campaign, `title`→title, `content_type`→content_type, `platform`→platform, `content_status`→content_status, `publish_date`→publish_date |
| `public.marketing_paid_ads` | KVH Marketing Ad | `campaign_id`→campaign, `ad_name`→ad_name, `platform`→platform, `spend`→spend, `leads`→leads, `impressions`→impressions, `clicks`→clicks |
| `public.marketing_subscriptions` | KVH Marketing Subscription | `vendor_name`→vendor_name, `plan_name`→plan_name, `cost`→cost, `billing_cycle`→billing_cycle, `next_renewal_date`→next_renewal_date, `status`→status |
| `public.marketing_invoices` | KVH Marketing Invoice | `invoice_number`→invoice_number, `client_id`→client, `invoice_date`→invoice_date, `due_date`→due_date, `period_from`→period_from, `period_to`→period_to, `status`→status, `subtotal`→subtotal, `discount`→discount, `tax_percent`→tax_percent, `tax_amount`→tax_amount, `total`→total, `amount_paid`→amount_paid, `balance`→balance |
| `public.marketing_invoice_items` | KVH Marketing Invoice Item | `kind`→kind, `description`→description, `quantity`→quantity, `unit_price`→unit_price, `amount`→amount |
| `public.marketing_invoice_payments` | KVH Marketing Invoice Payment | `paid_on`→paid_on, `amount`→amount, `method`→method, `reference`→reference |
| `public.marketing_mis_snapshots` | KVH Marketing MIS Snapshot | `period_year`→period_year, `period_month`→period_month, `status`→status, `budgeted_target`→budgeted_target, `afah_revenue`→afah_revenue, `auto_data`→auto_data(JSON) |

### Admin / System

| Supabase Table | Frappe DocType | Key Field Mappings |
|---|---|---|
| `public.notifications` | Notification Log | `user_id`→for_user, `title`→subject, `body`→email_content, `link`→document_name |
| `public.feature_flags` | KVH Feature Flag | `key`→name, `label`→label, `description`→description, `enabled`→enabled |
| `public.custom_field_definitions` | Custom Field | Recreate as Frappe Custom Fields per entity |
| `public.dropdown_options` | Select field options | Recreate as Select field option lists |
| `public.document_templates` | Letter Head | `company_name`→letter_head_name, `logo_url`→image, `gstin`→gstin, `company_address`→content |
| `public.service_tickets` | Issue | `ticket_number`→name(override), `status`→status |
| `public.number_series` | Naming Series | Recreate as ERPNext Naming Series |
| `public.fy_sequences` | Frappe Naming Series counter | ERPNext handles internally |
| `public.pdf_templates` | Print Format | Recreate as Frappe Print Formats |

---

## Relationship Type Mappings

| Supabase Pattern | Frappe Pattern |
|---|---|
| `FK(parent_table)` | `Link` field pointing to parent DocType |
| `ON DELETE CASCADE` child table | `Table` field (child DocType) |
| `ON DELETE RESTRICT` | ERPNext LinkValidation |
| `ON DELETE SET NULL` | Link field (nullable) |
| Many-to-many via junction table | Child DocType with two Link fields |
| `jsonb[]` arrays (simple values) | `Small Text` (comma-separated) or `JSON` field |
| `jsonb` structured data | Separate child table or `JSON` field |

## Trigger → Hook Mapping

| Supabase Trigger | Timing | Frappe Hook |
|---|---|---|
| `BEFORE INSERT OR UPDATE` | Pre-write | `validate()` method |
| `AFTER INSERT` | Post-create | `after_insert()` method |
| `AFTER UPDATE` | Post-save | `on_update()` method |
| `AFTER DELETE` | Post-delete | `on_trash()` method |
| SECURITY DEFINER function | Admin context | `frappe.flags.ignore_permissions = True` |
| `auth.uid()` in RLS | Current user | `frappe.session.user` |

## Supabase RLS → Frappe Permission

| Supabase RLS Policy Type | Frappe Equivalent |
|---|---|
| `USING(submitted_by = auth.uid())` | Permission level: owner only (no "Read All" perm) |
| `USING(has_role('Admin'))` | Role-based permission: only Admin role has access |
| `USING(true)` (all authenticated) | All logged-in roles have Read permission |
| `FOR SELECT` only policy | Read-only permission on role |
| `FOR ALL` admin policy | Full CRUD permission on Admin role |
| Branch-scoped: `AND branch = get_my_branch()` | Frappe doesn't have column RLS; use Permission Query Conditions |
