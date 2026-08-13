# KVH OS — Current System Feature Inventory

> **Document Purpose:** Comprehensive inventory of every feature, module, workflow, database entity, and automation present in the KVH Industries Operations Management System (KVH OS) as of the analysis date. This document is the authoritative source of truth for migration planning, gap analysis, and ERP scope definition.

---

## Application Overview

| Property | Value |
|---|---|
| **Company** | KVH Industries |
| **System Name** | KVH OS (Operations Management System) |
| **Platform** | Lovable / React + Supabase |
| **Frontend Framework** | React 19 + TanStack Router |
| **Build Tool** | Vite |
| **Styling** | TailwindCSS v4 + Radix UI |
| **Charts** | Recharts |
| **Backend / DB** | Supabase (PostgreSQL + Row Level Security) |
| **Authentication** | Supabase Auth + custom `profiles` table |
| **ID Format** | `KVH/MODULE/YY-YY/NNNN` (Fiscal-Year scoped) |
| **PDF Generation** | jsPDF + autotable (client-side) |
| **AI Integration** | AI SDK + OpenAI-compatible endpoint |
| **Storage** | Supabase Storage (branding, lead images) |

---

## User Roles

| Role | Code | Description | Key Permissions |
|---|---|---|---|
| Administrator | `Admin` | Full system access | All modules, user management, settings, feature flags, custom fields |
| Customer Relationship Executive | `CRE` | Front-line sales agent | Create orders, manage own leads/clients, submit weekly reports |
| Sales Head | `Sales_Head` | Manages all CREs | View all orders/leads, approve edit requests, set targets |
| Business Development Manager | `BDM` | Strategic sales role | Same capabilities as Sales_Head; campaign and lead visibility |
| Design Team | `Design_Team` | Manages design stages | Assign designers, update design status, submit design logs |
| Production Head | `Production_Head` | All production/factory | Approve payouts, access fabricator rate cards, MIS |
| Production Manager | `Production_Manager` | Factory operations management | Factory stage updates, MIS, rework visibility |
| Factory Supervisor | `Factory_Supervisor` | Specific fabricator oversight | Update stages, log reworks, manage fabricator jobs |
| Store Keeper | `Store_Keeper` | Inventory management | Stock transactions, audits, material transfers |
| Purchase Officer | `Purchase_Officer` | Procurement | PRs, RFQs, POs, supplier invoices, vendor management |
| Marketing Head | `Marketing_Head` | Marketing department | Campaigns, budgets, MIS snapshots, invoices |
| Marketing Member | `Marketing_Member` | Content and task contributor | Content creation, task updates, asset uploads |
| Operation Manager | `Operation_Manager` | Cross-functional visibility | Read access across modules, operations dashboards |
| HRMS Roles | Various | HR-specific functions | Staff management, leave, attendance, calendar |

---

## Number Series

| Series | Prefix | Format | Used For |
|---|---|---|---|
| Orders | `OR` | `KVH/OR/YY-YY/NNNN` | Sales orders |
| Leads | `LEAD` | `KVH/LEAD/YY-YY/NNNN` | Pre-sales leads |
| Customers | `CUS` | `KVH/CUS/YY-YY/NNNN` | SM customers |
| Purchase Orders | `PO` | `KVH/PO/YY-YY/NNNN` | Purchase orders |
| MRN | `MRN` | `KVH/MRN/YY-YY/NNNN` | Material receipt notes |
| Tickets | `TKT` | `KVH/TKT/YY-YY/NNNN` | Service desk tickets |
| Marketing Campaigns | `MC` | `KVH/MC/YY-YY/NNNN` | Campaign codes |
| Marketing Invoices | `MINV` | `KVH/MINV/YY-YY/NNNN` | Marketing invoices |
| Fabricator Payout Runs | `FPR` | `KVH/FPR/YY-YY/NNNN` | Payout run numbers |

**Database Tables:** `number_series` (module, label, prefix, fy_scoped, start_value), `fy_sequences` (prefix, fy, last_value)  
**DB Function:** `next_fy_id()` — generates the next sequential ID in `KVH/PREFIX/YY-YY/NNNN` format, scoped per fiscal year.

---

## Module 1: Orders & Production (Core)

### 1.1 Orders

| Property | Detail |
|---|---|
| **Module** | Orders & Production |
| **Feature** | Sales Order Management |
| **Users** | CRE (create), Sales_Head / BDM (approve edits, view all), Admin, Production roles (view) |
| **ID Format** | `KVH/OR/YY-YY/NNNN` |

#### Feature Table

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Order Creation | Create a new sales order with customer details, salesperson, amount, branch, finish type, delivery date | CRE, Admin | Requires customer name, amount, delivery date; generates ID via `next_fy_id()`; sets initial `payment_status = Payment Pending` | `sales_orders` | Draft → Payment Pending | Order Status PDF | `handle_new_user` creates profile; number series trigger assigns ID |
| Payment Gate | Block order from progressing if advance payment < 35% of order value | All (read), Admin (override) | If `amount_paid / amount < 0.35`, status remains `Payment Pending`; `override_approved_by` field allows bypass | `sales_orders.payment_status`, `sales_orders.override_approved_by` | Payment Pending → Advance Received → Fully Paid | Payment status on order | `enforce_payment_gate` DB trigger |
| Order Cancellation | Soft-cancel an order with a reason; records who cancelled and when | CRE (own), Sales_Head / BDM / Admin | Sets `status = Cancelled`; records `cancelled_at`, `cancelled_by`, `cancellation_reason`; no hard delete | `sales_orders` | Active → Cancelled | — | `notify_order_cancelled` trigger notifies salesperson |
| Order Edit Requests (CRE) | CRE requests permission to edit a submitted order | CRE (request), Sales_Head / BDM / Admin (approve) | Creates edit request record; approver sets expiry time; CRE can edit within expiry window only | `order_edit_requests` | Draft → Approved / Rejected | — | `notify_edit_request_created`, `notify_edit_request_decided` triggers |
| Order Edit Requests (Internal) | Production team requests internal edits to order data | Production_Manager / Factory_Supervisor (request), Production_Head / Admin (approve) | Separate request type from CRE edit requests; admin/production head approves | `internal_edit_requests` | Draft → Approved / Rejected | — | `notify_internal_edit_request`, `notify_internal_edit_decided` triggers |
| Order Status Progression | Order moves through defined lifecycle stages | Production roles, Admin | Stages advance automatically when all items complete final stage | `sales_orders.status` | Payment Pending → Pending Design → In Design → Pending CNC → In Fabrication → Ready for Delivery / Ready for Installation → Delivered → Cancelled | Order status dashboard | `auto_advance_order_status` trigger |
| Finish Type | Two finish types define the surface treatment applied | Admin / CRE (select) | `finish_type` ∈ {Primer Finish, Powder Coating}; affects factory_stage path | `sales_orders.finish_type` | — | — | — |
| Installation Flag | Toggle whether installation is included in the order | CRE / Admin | `include_installation = true` adds Installation stage to order item factory_stage path and routes to `Ready for Installation` | `sales_orders.include_installation` | — | — | `auto_advance_order_status` checks flag to choose ready status |
| Custom Fields | Admin-configurable extra fields on orders | Admin (configure), All (fill) | Fields defined in `custom_field_definitions` where `entity = sales_orders`; values in `custom_field_values` | `custom_field_definitions`, `custom_field_values` | — | — | — |
| PDF Generation | Generate customer-facing and internal documents | All relevant roles | Client-side generation via jsPDF + autotable; templates from `pdf_templates` | `pdf_templates` | — | Order Status PDF, Job Card PDF, Invoice PDF, Delivery Challan PDF | — |

**Key Fields — `sales_orders`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `order_number` | text | `KVH/OR/YY-YY/NNNN` |
| `customer_name` | text | — |
| `sales_person` | UUID FK → profiles | — |
| `amount` | numeric | Order value |
| `amount_paid` | numeric | Advance/total received |
| `ordered_date` | date | — |
| `committed_delivery_date` | date | — |
| `branch` | text | Multi-branch |
| `status` | text | Lifecycle stage |
| `payment_status` | text | Payment Pending / Advance Received / Fully Paid |
| `finish_type` | text | Primer Finish / Powder Coating |
| `include_installation` | boolean | — |
| `override_approved_by` | UUID FK → profiles | Payment gate bypass |
| `cancelled_at` | timestamptz | Soft cancel timestamp |
| `cancelled_by` | UUID FK → profiles | — |
| `cancellation_reason` | text | — |

---

### 1.2 Order Items

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Item Creation | Add product line items to an order | CRE, Admin | Each item has description, quantity, sheet/grill spec, installation method; links to parent order | `order_items` | Created → Pending | Job Card PDF | — |
| Designer Assignment | Assign a designer to an item | Design_Head (role implied by Sales_Head / Admin) | Sets `designer_assigned_to` FK; item appears in designer's queue | `order_items.designer_assigned_to` | Pending Design → In Design | Design workload | — |
| Design Status | Track design progress for each item | Design_Team, Designer | `design_status` ∈ {Pending, In Progress, Hold, Completed} | `order_items.design_status` | Pending → In Progress → Hold → Completed | Design MIS | — |
| Fabricator Assignment | Assign a fabricator (internal profile or external name) to an item | Factory_Supervisor, Production_Manager | `fabricator_assigned_to` FK for internal; `fabricator_name` text for external fabricators | `order_items.fabricator_assigned_to`, `order_items.fabricator_name` | — | Fabricator job list | — |
| Factory Stage Progression | Move item through production stages | Factory_Supervisor, Production_Manager | Stage sequence: Pending → CNC → Fabrication → Surface Finishing → Primer Coating / Powder Coating → PU Foam Filling → Accessories → Packing → Ready → Dispatched (→ Installation if flag set) | `order_items.factory_stage` | Per stage sequence | Production MIS, Stage count charts | `log_stage_events` trigger logs every transition |
| Stage Event Logging | Immutable log of every stage in/out/complete/assign event | Production roles (view) | Each stage entry/exit is recorded with timestamp, actor, event type | `order_item_stage_events` | — | Stage throughput metrics | `log_stage_events` trigger |
| Custom Fields on Items | Admin-configurable extra fields per item | Admin (configure), All (fill) | `entity = order_items` in `custom_field_definitions` | `custom_field_definitions`, `custom_field_values` | — | — | — |

**Key Fields — `order_items`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `order_id` | UUID FK → sales_orders | — |
| `product_description` | text | — |
| `quantity` | numeric | — |
| `sheet_spec` | text | Sheet specification |
| `grill_spec` | text | Grill specification |
| `installation_method` | text | — |
| `designer_assigned_to` | UUID FK → profiles | — |
| `fabricator_assigned_to` | UUID FK → profiles | Internal fabricator |
| `fabricator_name` | text | External fabricator name |
| `design_status` | text | Design lifecycle |
| `factory_stage` | text | Production stage |

---

### 1.3 Reworks

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Rework Logging | Log quality or production issues requiring rework | Factory_Supervisor, Production_Manager | Creates rework record linked to order and item; reason selected from seeded list | `reworks` | Open → In Progress → Resolved | Rework frequency report | — |
| Rework Reasons | Seeded picklist of standard rework reasons | Admin (manage) | Stored in `dropdown_options` category `rework_reasons`; seeded: Wrong measurement, Surface defect, Damaged in transit, Customer change, Quality rejection | `dropdown_options` | — | — | — |
| Feature Flag | Rework module can be toggled on/off | Admin | `feature_flags.key = rework_flow` | `feature_flags` | — | — | FeatureGate component |

**Key Fields — `reworks`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `order_id` | UUID FK → sales_orders | — |
| `item_id` | UUID FK → order_items | — |
| `reason` | text | From dropdown_options |
| `stage` | text | Stage at which rework occurred |
| `supervisor_id` | UUID FK → profiles | Who logged it |
| `status` | text | Open / In Progress / Resolved |

---

### 1.4 Design Module

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Design Head View | View all items awaiting/in design; assign designers | Production_Head, Admin | Filters items by `design_status`; bulk or individual assignment | `order_items` | — | Designer workload | — |
| Designer View | View own assigned items; update design status | Design_Team | Filtered by `designer_assigned_to = current_user` | `order_items` | — | — | — |
| Design Daily Logs | Designer submits daily area-based progress log | Design_Team | Records `drawn_sqft` and `undrawn_sqft` per day per designer | `design_logs` | — | Design throughput, daily progress | — |
| Design Log View | Heads view aggregated design log reports | Production_Head, Sales_Head | Aggregate by designer, date range | `design_logs` | — | Design MIS | — |

**Key Fields — `design_logs`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `designer_id` | UUID FK → profiles | — |
| `log_date` | date | — |
| `drawn_sqft` | numeric | Area designed |
| `undrawn_sqft` | numeric | Area pending |

---

### 1.5 Factory Module

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Factory Supervisor View | View items assigned to specific fabricators; update factory stages | Factory_Supervisor | Filtered by `fabricator_assigned_to` or `fabricator_name`; update `factory_stage` | `order_items` | Per stage | — | `log_stage_events` |
| Production MIS | Aggregate charts and metrics for production | Production_Head, Production_Manager, Operation_Manager | Stage-by-stage item count, throughput metrics, period filters | `order_items`, `order_item_stage_events` | — | Stage counts, throughput charts | — |
| Checklists | Factory checklists per stage or per item | Production roles | Route: `factory.checklists` | TBD | — | — | — |
| Production Filters | Filter factory view by stage, fabricator, date | Production roles | Multi-filter UI; by stage enum, by fabricator FK/name, by date range | `order_items` | — | — | — |

---

### 1.6 Delivery Module

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Delivery Tracking | Log delivery date, logistics partner, dispatch details | Production_Head, Operation_Manager | Records actual delivery date vs committed date; marks order Delivered | `sales_orders`, delivery records | Dispatched → Delivered | Delivery performance | — |
| Overdue Delivery Alerts | Banner alert for orders past committed delivery date | All relevant roles | Compares `committed_delivery_date` to today; renders alert banner | `sales_orders` | — | Overdue deliveries list | — |
| Delivery Management (Full) | Comprehensive delivery management screen | Production_Head, Operation_Manager | `delivery.tsx` (43KB); full delivery lifecycle | — | — | — | — |

---

### 1.7 Installation Module

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Installation Job Tracking | Manage jobs where `include_installation = true` | Production roles | Route: `installation.tsx` (23KB); separate from delivery | Installation records | Ready for Installation → Installed | — | — |
| Technician Assignment | Assign technician to installation job | Production_Manager | Links technician profile to installation record | Installation records | — | — | — |
| Installation Status | Track installation status per job | Production roles | Status progression per job | Installation records | — | — | — |
| Feature Flag | Installation module can be toggled | Admin | `feature_flags.key = installation_module` | `feature_flags` | — | — | FeatureGate component |

---

## Module 2: Pre-Sales / Lead Management

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Lead Creation | Create a new sales lead | CRE, Sales_Head, BDM, Admin | Auto-generates `KVH/LEAD/YY-YY/NNNN`; normalizes phone to last-10 digits as `phone_norm` | `leads` | new → contacted → ... | — | `leads_before_insupd` trigger: phone normalization, duplicate detection, number assignment |
| Lead Fields | Core lead data | All sales roles | name, phone, phone_norm, email, source, stage_key, owner_id, branch, place, notes, is_duplicate, merged_into_id, last_contacted_at, next_followup_at, ai_summary, location_lat/lng/url, converted_order_id, custom_fields | `leads` | — | — | — |
| Lead Stages | Configurable lifecycle stages | Admin, Sales_Head, BDM (configure); All (use) | Stages: new → contacted → qualified → proposal → negotiation → won / lost; each stage has color, terminal flag, won flag; fully configurable | `lead_stage_configs` | Stage progression | Conversion funnel | `log_lead_stage_change` trigger |
| Auto-Assignment | Round-robin auto-assignment of leads to CREs | System | Maintains assignment pointer in `lead_assignment_state`; triggers on lead insert | `lead_assignment_state`, `leads.owner_id` | — | — | `leads_auto_assign` trigger |
| Duplicate Detection | Detect duplicate leads by phone number | System, CRE (resolve) | On insert/update, checks `phone_norm` uniqueness; sets `is_duplicate = true`; links `merged_into_id` | `leads.is_duplicate`, `leads.merged_into_id` | — | Duplicate leads screen | `leads_before_insupd` trigger |
| Lead Merge | Merge duplicate leads into a master lead | Sales_Head, BDM, Admin | Sets `merged_into_id` on the duplicate; surfaces on Duplicate Leads management screen | `leads.merged_into_id` | — | Duplicate management screen | — |
| Lead Activities Log | Immutable log of key lead events | All (view) | Records `stage_change`, `owner_change`, `lead_created` events with actor and timestamp | `lead_activities` | — | — | `log_lead_stage_change` trigger |
| Lead Calls | Log inbound/outbound calls against a lead | CRE, Sales_Head | Records direction, outcome, duration_sec, notes, called_by; auto-updates `last_contacted_at` | `lead_calls` | — | Calls list view | `lead_call_bump_contact` trigger |
| Lead Follow-Ups | Schedule follow-up tasks for a lead | CRE, Sales_Head | Records due_at, note, assignee_id, status (Pending/Done); auto-syncs `next_followup_at` to lead record | `lead_followups` | — | Follow-up list | `lead_followup_sync` trigger |
| Lead Images | Attach photos to a lead | CRE, Sales_Head | Images stored in Supabase Storage; URLs linked to lead | `lead_images` | — | — | — |
| Lead Workflows | Trigger/action automation rules for leads | Admin (configure) | Configurable trigger + action rules (e.g., auto-assign on stage change) | `lead_workflows` | — | — | Workflow engine |
| Lead Custom Fields | Admin-configurable extra fields for leads | Admin (configure), All (fill) | `entity = leads` in `custom_field_definitions` | `custom_field_definitions`, `custom_field_values`, `leads.custom_fields` | — | — | — |
| AI Summary | Auto-generate AI summary of lead activity | System, CRE (trigger) | Calls AI SDK (OpenAI-compatible); writes to `leads.ai_summary` | `leads.ai_summary` | — | — | — |
| Pre-Sales Dashboard | KPIs and conversion funnel metrics | Sales_Head, BDM, Admin | Conversion rates, lead source breakdown, stage distribution | `leads`, `lead_activities` | — | KPIs, conversion funnel chart | — |
| Lead Settings | Configure stages, custom fields, lead sources | Admin, Sales_Head, BDM | Settings UI for stage config, custom fields, source picklist | `lead_stage_configs`, `custom_field_definitions`, `dropdown_options` | — | — | — |

**Key Fields — `leads`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `lead_number` | text | `KVH/LEAD/YY-YY/NNNN` |
| `name` | text | — |
| `phone` | text | Raw phone |
| `phone_norm` | text | Normalized last-10 digits |
| `email` | text | — |
| `source` | text | Lead source |
| `stage_key` | text | FK → lead_stage_configs |
| `owner_id` | UUID FK → profiles | Assigned CRE |
| `branch` | text | — |
| `place` | text | Location |
| `notes` | text | — |
| `is_duplicate` | boolean | — |
| `merged_into_id` | UUID FK → leads | Master lead |
| `last_contacted_at` | timestamptz | — |
| `next_followup_at` | timestamptz | — |
| `ai_summary` | text | AI-generated summary |
| `location_lat` | numeric | GPS latitude |
| `location_lng` | numeric | GPS longitude |
| `location_url` | text | Maps link |
| `converted_order_id` | UUID FK → sales_orders | If converted |
| `custom_fields` | jsonb | Dynamic custom data |

---

## Module 3: Sales Management

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| SM Teams | Define sales teams with a team lead and branch | Sales_Head, BDM, Admin | Each team has a `team_lead_id` and `branch`; CREs are members | `sm_teams` | — | Team performance | — |
| SM Team Members | Add/remove CREs from a team | Sales_Head, Admin | Links `user_id` to `team_id` with a `role_in_team` | `sm_team_members` | — | — | — |
| SM Customers | Manage customer master records | CRE (own), Sales_Head / BDM / Admin (all) | Customer number: `KVH/CUS/YY-YY/NNNN`; stores contact info, type, lead source, assigned CRE, team, architect/builder/contractor flags, links to clients and leads | `sm_customers` | — | Customer list | — |
| Customer Detail Page | Full customer history: orders, feedback, interactions | All sales roles | Aggregates all related records for a customer | `sm_customers`, `sales_orders`, `sm_feedback` | — | Customer 360 view | — |
| SM Feedback | Record customer feedback per order | CRE, Sales_Head | Records channel, rating (1–5), category, summary, action taken, follow-up required flag and date | `sm_feedback` | — | Feedback report | — |
| SM Targets | Set per-CRE sales targets | Sales_Head, BDM, Admin | Weekly/monthly targets: `target_amount`, `target_leads`, `target_quotations` | `sm_targets` | — | Target vs actual dashboard | — |
| SM Weekly Reports | CRE submits structured weekly performance report | CRE (submit), Sales_Head (review) | Status: Draft → Submitted → Presented; fields: auto_snapshot, overrides, key_learnings, escalations, head_involvement | `sm_weekly_reports` | Draft → Submitted → Presented | Weekly report list | — |
| Daily Sales Activity Logs | CREs log daily client-facing activities | CRE | Tracks visits, calls, meetings per day | Sales activity tables | — | Activity log | — |
| Quotations Tracking | Track formal price quotations sent to customers | CRE, Sales_Head | Links quotation to customer and potential order | Quotations table | — | Quotation pipeline | — |
| Follow-Ups Management | Manage all pending follow-up tasks for sales | CRE, Sales_Head | Aggregates follow-ups from leads and customers | `lead_followups`, follow-up tables | — | Follow-up queue | — |
| Sales MIS Dashboard | Comprehensive sales analytics | Sales_Head, BDM, Admin, Operation_Manager | Charts: revenue by CRE, conversion rates, daily activity, team comparisons | `sales_orders`, `leads`, `sm_targets`, `sm_weekly_reports` | — | Revenue charts, conversion funnel, activity heatmap | — |

**Key Fields — `sm_customers`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `customer_number` | text | `KVH/CUS/YY-YY/NNNN` |
| `name` | text | — |
| `mobile` | text | — |
| `whatsapp` | text | — |
| `email` | text | — |
| `district` | text | — |
| `state` | text | — |
| `customer_type` | text | — |
| `lead_source` | text | — |
| `assigned_cre_id` | UUID FK → profiles | — |
| `team_id` | UUID FK → sm_teams | — |
| `architect` | boolean | — |
| `builder` | boolean | — |
| `contractor` | boolean | — |

---

## Module 4: Sales Support

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Quotations Management | Create and manage formal quotations | CRE, Sales_Head | Separate from Sales Management; dedicated sales-support module routes | Sales support tables | — | Quotation PDF | — |
| Targets Tracking | View and track individual and team targets | CRE, Sales_Head | Reads from `sm_targets`; provides CRE-facing view | `sm_targets` | — | Target progress | — |
| Sales Support Routes | Dedicated route group for support tools | CRE, Sales_Head | `sales-support` route group in TanStack Router | — | — | — | — |

---

## Module 5: Clients

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Client Records | Maintain full client master data | CRE, Sales_Head, Admin | Early-stage `clients` table; linked to `sm_customers` | `clients` | — | Client list | — |
| Client Detail Page | View full order history and interactions for a client | CRE, Sales_Head, Admin | Aggregates all orders linked to the client | `clients`, `sales_orders` | — | Client history | — |

---

## Module 6: Procurement & Store

### 6.1 Vendors

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Vendor Master | Maintain vendor details including GST, contact, address, financial data | Purchase_Officer, Admin | Records: name, GST, email, phone, address (jsonb), opening_balance, on_time_pct, total_orders, active flag | `vendors` | — | Vendor list | — |
| Vendor Detail Page | Full transaction history for a vendor | Purchase_Officer, Admin | Aggregates POs, invoices, payments for the vendor | `vendors`, `purchase_orders`, `supplier_invoices` | — | Vendor ledger | — |

---

### 6.2 Purchase Requisitions (PR)

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| PR Creation | Raise a purchase requisition for materials | Any staff, Purchase_Officer | Records department, requester, needed_by date; auto-generates PR number | `purchase_requisitions`, `pr_items` | Draft → Approved / Rejected | — | — |
| PR Approval | Approve or reject a PR | Purchase_Officer, Admin | Sets `approver_id` and changes status; rejected PRs are closed | `purchase_requisitions.status`, `purchase_requisitions.approver_id` | Draft → Approved / Rejected / Closed | — | — |
| PR Items | Line items within a PR | Requester | item_name, quantity, unit, notes | `pr_items` | — | — | — |

---

### 6.3 RFQ (Request for Quotation)

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| RFQ Creation | Create an RFQ linked to an approved PR | Purchase_Officer | Auto-generates RFQ number; links to PR | `rfqs` | Open → Closed | — | — |
| Vendor Invitation | Invite multiple vendors to respond to an RFQ | Purchase_Officer | Many-to-many via `rfq_vendors`; tracks vendor response | `rfq_vendors` | — | — | — |
| Quotation Collection | Record vendor price responses | Purchase_Officer | Records item_name, quantity, unit, quoted_price, lead_time_days per vendor | `rfq_quotations` | — | — | — |
| Comparison View | Compare vendor quotes side by side | Purchase_Officer, Admin | Route: `purchase.compare`; sorts by price/lead time | `rfq_quotations` | — | Comparison report | — |
| RFQ PDF | Generate PDF of the RFQ to send to vendors | Purchase_Officer | Client-side via jsPDF | `pdf_templates` | — | RFQ PDF | — |

---

### 6.4 Purchase Orders (PO)

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| PO Creation | Create purchase order from accepted RFQ quotation | Purchase_Officer | PO number: `KVH/PO/YY-YY/NNNN`; vendor_name (text) + vendor_id (FK); status starts Draft | `purchase_orders`, `po_items` | Draft → Confirmed → MRN_Generated → Received → Cancelled | — | `assign_mrn_number` trigger |
| PO Status Progression | Move PO through lifecycle | Purchase_Officer, Store_Keeper | Draft → Confirmed → MRN_Generated → Received → Cancelled; MRN_Generated auto-creates stock transactions | `purchase_orders.status` | — | — | `auto_inward_po` trigger |
| MRN Generation | Material Receipt Note on goods receipt | Store_Keeper | MRN number: `KVH/MRN/YY-YY/NNNN`; triggers stock inward | `purchase_orders.mrn_number` | — | — | `auto_inward_po`, `apply_material_txn` triggers |
| PO Payment Tracking | Record payments against a PO | Purchase_Officer | Records amount, paid_on, method, notes; auto-recalculates `payment_status` | `po_payments`, `purchase_orders.payment_status` | Pending → Partial → Paid | — | `recalc_po_payment` trigger |
| PO PDF | Generate purchase order PDF | Purchase_Officer | Client-side via jsPDF; uses `pdf_templates` | `pdf_templates` | — | PO PDF | — |

**Key Fields — `purchase_orders`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `po_number` | text | `KVH/PO/YY-YY/NNNN` |
| `vendor_id` | UUID FK → vendors | Optional FK |
| `vendor_name` | text | Text fallback |
| `status` | text | Lifecycle stage |
| `payment_status` | text | Pending / Partial / Paid |
| `mrn_number` | text | `KVH/MRN/YY-YY/NNNN` |

---

### 6.5 Supplier Invoices

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Supplier Invoice | Record vendor invoices against POs | Purchase_Officer | Captures invoice_number, vendor, PO link, dates, line items, GST breakdown (CGST, SGST, IGST), totals | `supplier_invoices`, `supplier_invoice_items` | Draft → Verified → Paid → Cancelled | — | — |
| Invoice Settlement | Track amount paid and outstanding | Purchase_Officer | `amount_paid` tracked; status progresses to Paid when settled | `supplier_invoices.status`, `supplier_invoices.amount_paid` | — | — | — |

---

### 6.6 Debit Notes

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Debit Note Issuance | Issue a debit note to a vendor (for returns/discrepancies) | Purchase_Officer, Admin | Records vendor, invoice link, amount, reason, issued_on; auto-generates DN number | `debit_notes` | — | — | — |

---

### 6.7 Material Transfers

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Material Transfer Request | Request transfer of materials between locations | Store_Keeper, Production_Manager | Records from_location, to_location, items (jsonb); auto-generates transfer number | `material_transfers` | Requested → Dispatched → Received | — | — |

---

### 6.8 Inventory Items

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Item Master | Maintain inventory item catalogue | Store_Keeper, Admin | Fields: item_name, SKU (unique), category, unit_of_measurement, min_stock_level, branch, active | `inventory_items` | — | Item list | — |
| Stock Transactions | Record every stock movement | Store_Keeper, System | Transaction types: Inward, Outward, Floor_Issue, Floor_Return, Discrepancy, Branch_Issue, Branch_Return, Hinges_Inward, Hinges_Outward | `material_transactions` | — | Stock ledger | `apply_material_txn` trigger auto-updates `current_stock` |
| Stock Ledger | View full transaction history per item | Store_Keeper, Admin | Filterable by item, date, transaction type | `material_transactions` | — | Stock ledger report | — |
| Low Stock Alerts | Alert when stock falls below `min_stock_level` | Store_Keeper | Comparison at query/display time | `inventory_items.current_stock`, `inventory_items.min_stock_level` | — | Low stock report | — |

**Item Categories:** Raw_Material / Consumables / Machinery / Spares

---

### 6.9 Stock Audits

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Audit Creation | Plan a stock audit for a branch | Store_Keeper, Admin | Records branch, audit_date, status; auto-generates audit number | `stock_audits` | Planned → In Progress → Completed | — | — |
| Audit Lines | Record counted quantities vs system quantities | Store_Keeper | `variance = counted_qty − system_qty` (computed) | `stock_audit_lines` | — | Audit variance report | — |
| Audit Approval | Approve completed audit | Admin, Store_Keeper (supervisor) | Sets `approved_by` | `stock_audits.approved_by` | — | — | — |

---

### 6.10 Machinery Register

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Machinery Master | Register factory machinery | Production_Head, Admin | Records machine_name, location, status (Active / Under_Repair / Retired), purchased_on | `machinery_register` | Active → Under_Repair → Retired | Machinery list | — |
| Repair Logs | Log machinery breakdown and repair events | Factory_Supervisor, Production_Manager | Records issue_description, repair_cost, status (Logged / In_Progress / Resolved) | `machinery_repairs` | Logged → In_Progress → Resolved | — | `sync_machine_status` trigger: auto-sets machine status on repair insert/resolve |

---

### 6.11 Store Issues

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Direct Material Issue | Issue materials directly without a formal PO | Store_Keeper | Quick issue tracking for shop floor consumption | Store issue records | — | Issue log | — |
| Store Returns | Log return of unused materials to store | Store_Keeper | Records return quantity and reason | Store return records | — | Returns log | — |

---

## Module 7: Fabricators

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Fabricator Master | Maintain list of fabricators (internal/external) | Admin | `fabricators` table with name and active flag; seeded with default fabricators | `fabricators` | — | Fabricator list | — |
| Fabricator Rate Card | Per-product fabrication rates | Admin, Production_Head (write); Production_Head and above (read) | `product_key` normalized (lowercase, collapsed whitespace); rate per product type; active flag | `fabricator_rate_card` | — | Rate card view | — |
| Fabricator Jobs | View jobs assigned to each fabricator | Factory_Supervisor, Production_Manager | Reads from `order_items` filtered by fabricator | `order_items` | — | Jobs per fabricator | — |
| Payout Run Creation | Create a fabricator payout run for a period | Production_Head, Admin | Run number: `KVH/FPR/YY-YY/NNNN`; records fabricator, period_start, period_end, mode (Auto/Manual) | `fabricator_payout_runs` | Draft → Approved → Paid → Cancelled | — | — |
| Payout Lines | Auto or manually populate payout line items | Production_Head, Admin | Each line: item_id, order_id, product_description, product_key, quantity, rate (from rate card), amount (qty × rate); rate_override and note possible | `fabricator_payout_lines` | — | — | `recalc_payout_run` trigger: auto-recalculates run totals on line insert/update/delete |
| Payout Line Lock Guard | Prevent editing lines on approved/paid runs | System | DB trigger prevents any DML on lines when run status is Approved or Paid | `fabricator_payout_runs.status`, `fabricator_payout_lines` | — | — | `guard_payout_line_lock` trigger |
| Payout Approval | Approve a draft payout run | Production_Head | Sets status = Approved; prevents further editing of lines | `fabricator_payout_runs.status` | Draft → Approved | — | — |
| Payout Payment | Mark a run as paid | Admin, Production_Head | Records `paid_at`, `paid_reference`; sets status = Paid | `fabricator_payout_runs` | Approved → Paid | — | — |
| Fabricator Computation PDF | Generate computation sheet per fabricator | Production_Head, Admin | Client-side jsPDF; itemized qty × rate breakdown | `pdf_templates` | — | Computation PDF | — |
| Fabricator Payout PDF | Generate payout summary PDF | Production_Head, Admin | Client-side jsPDF; summary per run | `pdf_templates` | — | Payout PDF | — |

**Key Fields — `fabricator_payout_runs`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `run_number` | text | `KVH/FPR/YY-YY/NNNN` |
| `fabricator_id` | UUID FK → fabricators | — |
| `period_start` | date | — |
| `period_end` | date | — |
| `mode` | text | Auto / Manual |
| `status` | text | Draft / Approved / Paid / Cancelled |
| `total_items` | integer | — |
| `total_qty` | numeric | — |
| `total_amount` | numeric | — |
| `approved_by` | UUID FK → profiles | — |
| `paid_at` | timestamptz | — |
| `paid_reference` | text | Payment ref |

---

## Module 8: Incentives

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Incentive Rules | Define monthly tier-based incentive rules | Admin | `effective_month` (unique date); `tiers` jsonb array of sales brackets with incentive amounts; `updated_by` tracks last editor | `incentive_rules` | — | — | — |
| Incentive Calculation | Calculate per-CRE incentive based on monthly sales | Sales_Head, Admin, CRE (own) | `incentives.tsx` (35KB); reads monthly order amounts per CRE vs current month's tier structure; computes incentive amount | `incentive_rules`, `sales_orders` | — | Per-CRE incentive report | — |
| Feature Flag | Incentives page can be toggled on/off | Admin | `feature_flags.key = incentives_page` | `feature_flags` | — | — | FeatureGate component |

---

## Module 9: Marketing

### 9.1 Marketing Clients

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Marketing Client Master | Maintain external marketing clients | Marketing_Head, Admin | Records: name, contact, email, notes, active flag, monthly_retainer amount | `marketing_clients` | — | Client list | — |

---

### 9.2 Marketing Campaigns

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Campaign Creation | Create a marketing campaign | Marketing_Head, Admin | Campaign code: `KVH/MC/YY-YY/NNNN`; assigns client, sub_team, status, dates, budget, platforms[], owner | `marketing_campaigns` | Draft → Internal Review → Client Approval → Approved → Live → Completed → Cancelled | Campaign dashboard | — |
| Campaign Status Flow | Track campaign through approval and execution stages | Marketing_Head, Marketing_Member | Status transitions controlled by approvals and manual updates | `marketing_campaigns.status` | Per status above | — | `sync_marketing_approval` trigger |

**Sub-Teams:** Social Media / Performance / Design / Video / Website & SEO / General

---

### 9.3 Marketing Content Items

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Content Item Creation | Create content items within a campaign | Marketing_Member, Marketing_Head | Records title, content_type, platform, sub_team, designer/creator assignment, status, publish_date, asset_url | `marketing_content_items` | Idea → Drafting → Designing → Internal Review → Client Review → Approved → Scheduled → Published → Cancelled | Content calendar | — |
| Content Approval | Approve or reject content items | Marketing_Head (internal), Client (external) | Approval record created; `sync_marketing_approval` updates content status automatically | `marketing_approvals` | Per content status | — | `sync_marketing_approval` trigger |

**Content Types:** Post / Reel / Story / Video / Blog / Ad / Email / Other

---

### 9.4 Marketing Paid Ads

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Paid Ad Tracking | Log paid advertising campaigns | Marketing_Head, Marketing_Member | Records ad_name, platform, spend, leads, impressions, clicks, dates, status | `marketing_paid_ads` | Planned → Live → Paused → Completed → Cancelled | Ad performance dashboard | — |

---

### 9.5 Marketing Brand Assets

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Brand Asset Library | Store and tag brand assets | Marketing_Member, Marketing_Head | Records name, asset_type, file_url (Supabase Storage), tags[], client_id | `marketing_brand_assets` | — | Asset library | — |

---

### 9.6 Marketing Subscriptions

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Subscription Tracking | Track SaaS and tool subscriptions used by marketing | Marketing_Head, Admin | Records vendor, plan, category, cost, billing_cycle, next_renewal_date, status | `marketing_subscriptions` | Active → Paused → Cancelled | Renewal calendar | — |

**Billing Cycles:** Monthly / Quarterly / Yearly / One-time

---

### 9.7 Marketing Budget

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Budget Entries | Track planned vs actual campaign spend | Marketing_Head, Admin | Records campaign, category, description, amount, entry_type (Planned/Actual), entry_date | `marketing_budget_entries` | — | Budget vs actual | — |

---

### 9.8 Marketing Tasks

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Task Management | Create and manage marketing tasks | Marketing_Member, Marketing_Head | Records title, description, assignee, sub_team, related_type/related_id, status, due_date | `marketing_tasks` | Todo → In Progress → Blocked → Done → Cancelled | Task board | — |
| Recurring Tasks | Auto-generate repeating tasks | Marketing_Head | `is_recurring = true`; `recurrence_rule` jsonb defines schedule; `parent_task_id` links series | `marketing_tasks` | — | — | — |

---

### 9.9 Marketing Approvals

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Approval Workflow | Route campaigns and content through approval steps | Marketing_Head (internal), Client (external) | entity_type (campaign/content/ad), entity_id, step (Internal Review/Client Approval), status (Pending/Approved/Rejected) | `marketing_approvals` | Pending → Approved / Rejected | Approval queue | `sync_marketing_approval` trigger: auto-updates campaign/content status + sends notification |

---

### 9.10 Marketing SOPs

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| SOP Library | Store standard operating procedures per sub-team | Marketing_Head, Admin | Records sub_team, body (rich text), version, active flag | `marketing_sops` | — | SOP directory | — |

---

### 9.11 Marketing Invoices

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Invoice Creation | Generate invoices for marketing clients | Marketing_Head, Admin | Invoice number: `KVH/MINV/YY-YY/NNNN`; links to client, period, line items; tax = 18% | `marketing_invoices`, `marketing_invoice_items` | Draft → Sent → Partially Paid → Paid → Cancelled | Invoice PDF | `recalc_marketing_invoice` trigger: auto-recalculates totals on item/payment change |
| Invoice Payments | Record payments against marketing invoices | Marketing_Head, Admin | Records paid_on, amount, method, reference; auto-recalcs balance and status | `marketing_invoice_payments` | — | — | `recalc_marketing_invoice` trigger |
| Public Invoice URL | Share invoice with client via secure token URL | Marketing_Head | Route: `marketing-invoice.$token`; no login required; token-authenticated | `marketing_invoices` | — | — | — |
| Invoice Fields | Key financial fields | — | subtotal, discount, tax_percent (18%), tax_amount, total, amount_paid, balance | `marketing_invoices` | — | — | — |

**Invoice Item Kinds:** Retainer / Ad Spend / Subscription / Service / Other

---

### 9.12 Marketing MIS

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| MIS Snapshot | Monthly management information snapshot | Marketing_Head, Admin | Records period_year, period_month, status (Draft/Final); includes overrides for team cost, tools cost, sales; budgeted_target (default 7,500,000); afah_revenue; auto_data jsonb; notes | `marketing_mis_snapshots` | Draft → Final | MIS dashboard | — |
| MIS Salesperson Rows | Per-salesperson revenue attribution in MIS | Marketing_Head | Records display_name, sales_amount, sales_ratio_percent | `marketing_mis_salesperson_rows` | — | MIS sales breakdown | — |

---

## Module 10: HRMS

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Staff Management | Full staff profile and HR record management | HRMS roles, Admin | Routes: `hrms.staff.index`, `hrms.staff.$staffId`; extended HR data beyond auth profile | Staff tables | — | Staff directory | — |
| HR Calendar | Calendar view for leave, attendance, events | HRMS roles, Admin | Route: `hrms.calendar` (25KB); visual calendar interface | HR calendar tables | — | Attendance calendar | — |
| Leave Management | Manage leave requests and approvals | Staff, HRMS roles | Leave request → approval workflow | Leave tables | Submitted → Approved / Rejected | Leave report | — |
| Attendance Tracking | Log and track staff attendance | HRMS roles | Daily attendance records | Attendance tables | — | Attendance report | — |
| Team Roster | View team scheduling and availability | HRMS roles, Managers | Route: `team-roster` | Roster tables | — | Team roster view | — |

---

## Module 11: Service Desk

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Ticket Creation | Raise a customer service ticket | CRE, Customer, Admin | Ticket number: `KVH/TKT/YY-YY/NNNN`; auto-assigned via `assign_ticket_number` trigger | `service_tickets` | Open → In Progress → Resolved / Closed | — | `assign_ticket_number` trigger |
| Ticket Status Tracking | Track ticket progress to resolution | Support roles, Admin | Route: `service-desk.tsx` (13KB) | `service_tickets.status` | Per status | Ticket list, resolution time | — |

**Key Fields — `service_tickets`:**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | — |
| `ticket_number` | text | `KVH/TKT/YY-YY/NNNN` |
| `status` | text | Lifecycle status |

---

## Module 12: Accounts

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Financial Accounts | Core accounts management interface | Admin, Finance roles | Route: `accounts.tsx` (6KB) | Accounts tables | — | Accounts summary | — |
| Receipts | Record and view payment receipts | Admin, Finance | `ReceiptsCard` component | Receipts table | — | Receipts log | — |
| Refunds | Record and manage refunds | Admin, Finance | `RefundsCard` component | Refunds table | — | Refunds log | — |

---

## Module 13: Workspace

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Personal Dashboard | Individual KPI view and daily summary | All users | Route: `workspace.index`; personalized to logged-in user | `sales_orders`, `leads`, personal tables | — | Personal KPIs | — |
| Personal Task Management | Create and manage personal to-do tasks | All users | Route: `workspace.tasks` | Personal tasks table | Todo → Done | — | — |
| Personal Notes | Take and save personal notes | All users | Route: `workspace.notes` | Personal notes table | — | — | — |
| Personal Calendar | Personal schedule and event view | All users | Route: `workspace.calendar` | Personal calendar table | — | — | — |

---

## Module 14: Admin Panel

### 14.1 User & Role Management

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| User Creation | Create new system users | Admin | Creates Supabase auth user + profile; assigns roles[] array and branch | `profiles` | — | User list | `handle_new_user` trigger |
| User Activation / Deactivation | Enable or disable user access | Admin | Sets active flag on profile; deactivated users cannot log in | `profiles.active` | — | — | — |
| Role Assignment | Assign one or more roles to a user | Admin | Multi-role support via `profiles.roles[]` array | `profiles.roles` | — | — | — |
| Branch Assignment | Assign user to one or more branches | Admin | Controls data visibility via RLS policies | `profiles.branch` | — | — | — |
| Permission Matrix | Fine-grained permission editing | Admin | `EditPermissionPanel` component; per-role capability matrix | Role permission tables | — | — | — |

---

### 14.2 System Settings

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| General Settings | System-wide configuration | Admin | Company details, defaults | Settings tables | — | — | — |
| Branches Management | Add/edit branches for multi-branch support | Admin | All orders, users, inventory scoped to branches | `branches` table | — | — | — |
| Email Notifications | Configure email notification triggers and templates | Admin | Per-event email configuration | Notification config tables | — | — | — |
| Integrations | Configure external system integrations | Admin | AI SDK endpoint, storage settings | Integration config | — | — | — |
| Backup & Restore | System data backup and restoration | Admin | Export/import system data | — | — | — | — |
| CSV Import | Bulk import data via CSV upload | Admin | Route: `import` (10KB); maps CSV columns to DB fields | — | — | — | — |
| Security Settings | Password policies, session management | Admin | — | Security config | — | — | — |
| Profile Settings | Manage own profile details | All users | Update name, contact, preferences | `profiles` | — | — | — |
| Audit Logs | View system-wide audit trail | Admin | Route: `admin.settings.audit`; records actions across modules | Audit log tables | — | Audit report | — |
| Customization | Manage custom fields and dropdown options | Admin | Links to `custom_field_definitions` and `dropdown_options` | `custom_field_definitions`, `dropdown_options` | — | — | — |
| Automation Settings | Configure workflow automation rules | Admin | Trigger/action rule management | `lead_workflows` | — | — | — |
| Preferences | UI and system preferences | Admin, All users | Theme, locale, notification preferences | Preferences tables | — | — | — |

---

### 14.3 Roles Management

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Role Management | Create, view, and edit system roles | Admin | Route: `admin.settings.roles.tsx` (8KB); role permission matrix | Role tables | — | — | — |
| Permission Matrix | Define what each role can do per module | Admin | Grid UI; per-role, per-module create/read/update/delete flags | Role permission tables | — | — | — |

---

### 14.4 SLA Management

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| SLA Rules | Define SLA targets for tickets or orders | Admin | Route: `admin.sla.tsx` (21KB); per entity type, per priority | SLA rule tables | — | — | — |
| SLA Tracking | Monitor compliance against SLA rules | Admin, Operation_Manager | Compares actual resolution time vs SLA target | SLA tracking tables | — | SLA compliance report | — |
| Overdue Detection & Escalation | Auto-detect and escalate overdue SLA breaches | System, Admin | Periodic checks against SLA rules; escalation routing | SLA tracking, notifications | — | Overdue SLA report | — |

---

### 14.5 Dropdown Options

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Dropdown Management | Admin-configurable picklists for select fields across the system | Admin | Categories: factory_stages, stage_status, order_status, rework_reasons; fields: category, value, sort_order, active | `dropdown_options` | — | — | — |

---

## Module 15: Feature Flags

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Feature Flag Management | Enable or disable optional system features | Admin | Toggle flags; React `FeatureGate` component conditionally renders gated features based on flag state | `feature_flags` | — | — | — |

**Active Flags:**

| Flag Key | Label | Effect |
|---|---|---|
| `incentives_page` | Incentives Page | Show/hide incentives module |
| `rework_flow` | Rework Flow | Enable rework logging and tracking |
| `cnc_stage` | CNC Stage | Include CNC as distinct factory stage |
| `installation_module` | Installation Module | Enable installation job management |

**Key Fields — `feature_flags`:**

| Field | Type | Notes |
|---|---|---|
| `key` | text PK | Unique flag key |
| `label` | text | Human-readable name |
| `description` | text | What the flag controls |
| `enabled` | boolean | Current state |

---

## Module 16: Custom Fields

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Field Definition | Admin defines extra fields on entities | Admin | Entities: sales_orders / order_items / clients / reworks; field types: text / textarea / number / date / select / checkbox; options (jsonb for select); required flag; sort_order | `custom_field_definitions` | — | — | — |
| Field Values | Store user-entered values for custom fields | All (fill) | Values keyed by (field_id, entity, record_id); value stored as jsonb | `custom_field_values` | — | — | — |
| Dynamic UI | React component renders custom fields dynamically | All | `CustomFieldsSection` component reads definitions and renders appropriate inputs | — | — | — | — |

---

## Module 17: Notifications

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| In-App Notifications | Bell icon shows unread notifications to each user | All | `NotificationsBell` React component; polls/subscribes for unread count | `notifications` | — | — | Various DB triggers |
| Notification Record | Each notification: user_id, title, body, link, read flag, created_at | System (create), User (mark read) | User-scoped; `read = false` for new; user marks as read | `notifications` | — | — | — |

**Trigger Sources:**

| Event | Trigger |
|---|---|
| Order completion | `auto_advance_order_status` |
| Order cancellation | `notify_order_cancelled` |
| Edit request created (CRE) | `notify_edit_request_created` |
| Edit request decided | `notify_edit_request_decided` |
| Internal edit request created | `notify_internal_edit_request` |
| Internal edit request decided | `notify_internal_edit_decided` |
| Marketing approval decision | `sync_marketing_approval` |

---

## Module 18: Number Series

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Number Series Config | Define prefix, start value, and FY-scope settings per module | Admin | `number_series` table stores config per module; `fy_scoped = true` means counter resets each fiscal year | `number_series` | — | — | — |
| FY Sequence Tracking | Track current last_value per prefix+FY combination | System | `fy_sequences` increments atomically on each call | `fy_sequences` | — | — | — |
| ID Generation Function | DB function generates next ID in standard format | System | `next_fy_id(prefix)` produces `KVH/PREFIX/YY-YY/NNNN`; called by various triggers and application code | PostgreSQL function | — | — | Called by: `assign_mrn_number`, `assign_ticket_number`, `leads_before_insupd`, and all module insert triggers |

---

## Module 19: Audit & Activity

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Lead Activities Log | Tracks key lead lifecycle events | All (view), System (write) | Types: stage_change, owner_change, lead_created; immutable once written | `lead_activities` | — | Lead history timeline | `log_lead_stage_change` trigger |
| Order Item Stage Events | Tracks every production stage transition | Production roles (view), System (write) | Event types: in / out / completed / assigned; records actor and timestamp per stage | `order_item_stage_events` | — | Stage throughput analysis | `log_stage_events` trigger |
| Admin Audit Log View | View system-wide admin actions | Admin | Route: `admin.settings.audit`; reads from audit tables | Audit tables | — | Audit report | `set_updated_at` trigger on all tables |

---

## Module 20: PDF Templates

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| PDF Template Config | Admin configures branding and layout of each PDF document type | Admin | Per-doc settings: branding, header, footer, layout, sections, columns — all jsonb; one row per `doc_type` (unique) | `pdf_templates` | — | — | — |
| Client-Side PDF Generation | Generate PDFs in the browser using jsPDF + autotable | All relevant roles | Reads `pdf_templates` for the doc_type; applies company branding from `document_templates` | `pdf_templates`, `document_templates` | — | — | — |

**PDF Document Types:**

| doc_type | Description |
|---|---|
| `order_status` | Customer-facing order status copy |
| `purchase_order` | Purchase order sent to vendor |
| `quote` | Quotation document |
| `invoice` | Customer invoice |
| `job_card` | Internal factory job card |
| `dc` | Delivery challan |
| `fabricator_computation` | Fabricator itemized computation |
| `fabricator_payout` | Fabricator payout summary |
| `table_export` | Generic table data export |

---

## Document Templates & Branding

| Feature | Description | Users | Business Logic | Database | Workflow | Reports | Automation |
|---|---|---|---|---|---|---|---|
| Company Branding | Configure company identity for all generated documents | Admin | Singleton row (key = `default`): company_name, company_address, GSTIN, logo_url, letterhead_html, footer_terms | `document_templates` | — | — | — |
| Branding Storage | Store logo and letterhead assets | Admin | Supabase Storage bucket `branding`; logo_url references stored asset | Supabase Storage | — | — | — |

---

## Integrations

| Integration | Type | Purpose | Status |
|---|---|---|---|
| Supabase Auth | Authentication | Email/password login, session management | Active |
| Supabase Storage | File Storage | Branding assets, lead images | Active |
| AI SDK (OpenAI-compatible) | AI | Lead AI summary generation | Active |
| jsPDF + autotable | PDF | Client-side PDF generation for all document types | Active |
| WhatsApp | Messaging | — | **Not found in codebase** |
| Payment Gateway | Payments | — | **Not found in codebase** |
| Public Invoice Token | Public URL | Marketing invoice sharing without login | Active |

---

## Database Automations — Triggers & Functions

The following PostgreSQL triggers automate critical business logic in KVH OS. All triggers run server-side in Supabase, ensuring consistency regardless of which client or role performs the action.

| # | Trigger Name | Event | Table | Action |
|---|---|---|---|---|
| 1 | `handle_new_user` | AFTER INSERT | `auth.users` | Auto-create a row in `profiles` for new Supabase auth signup |
| 2 | `enforce_payment_gate` | BEFORE UPDATE | `sales_orders` | Set `status = Payment Pending` if `amount_paid / amount < 0.35` unless `override_approved_by` is set |
| 3 | `auto_advance_order_status` | AFTER UPDATE | `order_items` | When all items reach final factory_stage, advance parent order to `Ready for Delivery` or `Ready for Installation`; notify salesperson |
| 4 | `auto_inward_po` | AFTER UPDATE | `purchase_orders` | Auto-create `material_transactions` (Inward) when PO status changes to `MRN_Generated` or `Received` |
| 5 | `apply_material_txn` | AFTER INSERT | `material_transactions` | Auto-update `inventory_items.current_stock` based on transaction type (add for Inward, subtract for Outward, etc.) |
| 6 | `recalc_po_payment` | AFTER INSERT/DELETE | `po_payments` | Auto-recalculate `purchase_orders.payment_status` (Pending / Partial / Paid) based on sum of payments |
| 7 | `sync_machine_status` | AFTER INSERT/UPDATE | `machinery_repairs` | Auto-update `machinery_register.status` to `Under_Repair` on new repair; to `Active` on Resolved |
| 8 | `recalc_payout_run` | AFTER INSERT/UPDATE/DELETE | `fabricator_payout_lines` | Auto-recalculate `fabricator_payout_runs.total_items`, `total_qty`, `total_amount` |
| 9 | `guard_payout_line_lock` | BEFORE INSERT/UPDATE/DELETE | `fabricator_payout_lines` | Raise exception if parent run status is Approved or Paid; prevents editing locked runs |
| 10 | `sync_marketing_approval` | AFTER UPDATE | `marketing_approvals` | Auto-update campaign or content status based on approval decision; insert notification for relevant users |
| 11 | `recalc_marketing_invoice` | AFTER INSERT/UPDATE/DELETE | `marketing_invoice_items`, `marketing_invoice_payments` | Auto-recalculate `marketing_invoices` totals: subtotal, tax_amount, total, amount_paid, balance; update status |
| 12 | `leads_before_insupd` | BEFORE INSERT/UPDATE | `leads` | Normalize `phone_norm` (last-10 digits); detect duplicates by `phone_norm`; assign `lead_number` via `next_fy_id()` on insert |
| 13 | `leads_auto_assign` | AFTER INSERT | `leads` | Round-robin assign new lead to next available CRE using `lead_assignment_state` pointer |
| 14 | `log_lead_stage_change` | AFTER UPDATE | `leads` | Insert record into `lead_activities` on `stage_key` or `owner_id` change |
| 15 | `lead_call_bump_contact` | AFTER INSERT | `lead_calls` | Update `leads.last_contacted_at` to call timestamp |
| 16 | `lead_followup_sync` | AFTER INSERT/UPDATE | `lead_followups` | Sync `leads.next_followup_at` to the earliest Pending follow-up `due_at` |
| 17 | `log_stage_events` | AFTER UPDATE | `order_items` | Insert record into `order_item_stage_events` on `factory_stage` change; records in/out/completed/assigned event type |
| 18 | `notify_order_cancelled` | AFTER UPDATE | `sales_orders` | Insert notification for salesperson when `status` changes to `Cancelled` |
| 19 | `notify_edit_request_created` | AFTER INSERT | `order_edit_requests` | Insert notifications for Admin, Sales_Head, BDM when CRE creates an edit request |
| 20 | `notify_edit_request_decided` | AFTER UPDATE | `order_edit_requests` | Insert notification for requesting CRE when edit request is Approved or Rejected |
| 21 | `notify_internal_edit_request` | AFTER INSERT | `internal_edit_requests` | Insert notifications for Admin, Production_Head when production team requests internal edit |
| 22 | `notify_internal_edit_decided` | AFTER UPDATE | `internal_edit_requests` | Insert notification for requester when internal edit request is decided |
| 23 | `assign_mrn_number` | BEFORE INSERT | `purchase_orders` | Auto-assign `KVH/MRN/YY-YY/NNNN` via `next_fy_id()` |
| 24 | `assign_ticket_number` | BEFORE INSERT | `service_tickets` | Auto-assign `KVH/TKT/YY-YY/NNNN` via `next_fy_id()` |
| 25 | `set_updated_at` | BEFORE UPDATE | All major tables | Set `updated_at = now()` on every row update; used for audit trail and ordering |

---

## React Component Inventory — Key Components

| Component / File | Size | Purpose |
|---|---|---|
| `delivery.tsx` | 43 KB | Full delivery management screen |
| `incentives.tsx` | 35 KB | Incentive calculation and display |
| `hrms.calendar` | 25 KB | HR calendar view |
| `installation.tsx` | 23 KB | Installation job management |
| `admin.sla.tsx` | 21 KB | SLA rules and tracking |
| `service-desk.tsx` | 13 KB | Service ticket management |
| `import` route | 10 KB | CSV bulk import |
| `admin.settings.roles.tsx` | 8 KB | Role management |
| `accounts.tsx` | 6 KB | Financial accounts |
| `FeatureGate` | — | Conditionally render features based on flag state |
| `CustomFieldsSection` | — | Render dynamic custom fields per entity |
| `NotificationsBell` | — | In-app notification bell with unread count |
| `EditPermissionPanel` | — | Per-role permission matrix editor |
| `ReceiptsCard` | — | Receipts display in Accounts |
| `RefundsCard` | — | Refunds display in Accounts |

---

## TanStack Router Route Groups

| Route Group | Modules |
|---|---|
| `orders.*` | Orders, order items, delivery, installation |
| `factory.*` | Factory supervisor views, checklists, production MIS |
| `purchase.*` | PRs, RFQs, POs, comparison, supplier invoices |
| `leads.*` | Lead list, lead detail, calls, follow-ups, duplicates, settings |
| `sales-support.*` | Quotations, targets |
| `marketing.*` | Campaigns, content, ads, invoices, MIS, brand assets |
| `hrms.*` | Staff, calendar, leave, team roster |
| `admin.*` | Users, roles, settings, SLA, audit |
| `workspace.*` | Personal dashboard, tasks, notes, calendar |
| `service-desk` | Tickets |
| `accounts` | Financial accounts |
| `fabricators.*` | Fabricator management, payout runs |
| `marketing-invoice.$token` | Public invoice (no auth required) |

---

## Data Security Model

| Mechanism | Implementation |
|---|---|
| **Row Level Security (RLS)** | All Supabase tables protected with RLS policies |
| **Role-based data scoping** | CRE sees own data; Sales_Head sees all; RLS enforces this |
| **Branch scoping** | Users scoped to branch; RLS filters by branch where applicable |
| **Auth** | Supabase Auth (JWT); all API calls include auth token |
| **Storage** | Supabase Storage with access policies on branding and lead image buckets |
| **Public token** | Marketing invoice public URL uses secure random token; no auth session required |

---

## Known Gaps / Not Yet Implemented

| Capability | Status |
|---|---|
| WhatsApp integration | Not found in codebase |
| Payment gateway integration | Not found in codebase |
| SMS notifications | Not documented |
| Mobile application | Not found; web-only system |
| Multi-currency support | Not documented |
| E-way bill / GST filing integration | Not documented |
| Advanced GL / Double-entry accounting | Not found; Accounts module is basic (receipts + refunds) |

---

*Document generated: 2026-08-11 | KVH OS Current System Feature Inventory v1.0*
