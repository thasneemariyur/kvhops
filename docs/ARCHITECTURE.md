# KVH Operations — ERPNext Migration Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    KVH INDUSTRIES ERP SYSTEM                   │
│                 (ERPNext 15 + Frappe 15 + kvh_ops)             │
├────────────────────────────────────────────────────────────────┤
│  FRONTEND: Frappe Desk (Vue.js based)                          │
│  ● Standard ERPNext modules (Accounts, Buying, Stock, HR)      │
│  ● Custom workspaces and dashboards                            │
│  ● Custom forms and views via kvh_ops app                      │
├─────────────────────┬──────────────────────────────────────────┤
│  CUSTOM APP         │  STANDARD ERPNEXT MODULES                │
│  kvh_ops            │                                          │
│  ─────────────────  │  ● Accounts (Payment Entry, Invoices)    │
│  Custom DocTypes:   │  ● Buying (PO, RFQ, Supplier)            │
│  KVH Job Card       │  ● Selling (Sales Order, Quotation)      │
│  KVH Fabricator     │  ● Stock (Item, Warehouse, Stock Entry)  │
│  KVH Fabricator     │  ● CRM (Lead, Opportunity, Campaign)     │
│    Payout           │  ● HR (Employee, Leave, Attendance)      │
│  KVH Rework         │  ● Support (Issue / Service Desk)        │
│  KVH Order Edit     │  ● Projects (Task, Timesheet)            │
│    Request          │  ● Manufacturing (Work Order, BOM)       │
│  KVH Marketing      ├──────────────────────────────────────────┤
│    Invoice          │  STANDARD FRAPPE                         │
│  KVH Marketing      │  ● User, Role, Permission               │
│    Campaign         │  ● Workflow, Notification               │
│  KVH Incentive Rule │  ● Activity Log, ToDo                   │
│  KVH Sales Target   │  ● File, Attachment                     │
│  KVH Weekly Report  │  ● Letter Head, Print Format            │
│  KVH Feature Flag   │  ● Email, SMS                           │
│  KVH SLA Rule       │  ● Assignment Rule                      │
│  + 25 more          │  ● Naming Series                        │
├─────────────────────┴──────────────────────────────────────────┤
│  BUSINESS LOGIC LAYER (Python / Frappe Hooks)                  │
│  ● Sales Order hooks: payment gate, job card creation          │
│  ● CRM Lead hooks: phone normalization, auto-assign, AI        │
│  ● PO hooks: MRN generation, stock auto-inward                 │
│  ● Fabricator Payout: lock guard, auto-recalculate             │
│  ● Marketing Invoice: GST calc, payment status, public token   │
│  ● Scheduled tasks: overdue alerts, SLA checks, renewals       │
├────────────────────────────────────────────────────────────────┤
│  DATA LAYER: MariaDB 10.6+ (Frappe standard)                   │
│  ● Frappe DocType tables (tab{DocType})                        │
│  ● Naming series tables                                        │
│  ● Activity logs, file storage                                 │
├────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                                │
│  ● Nginx (reverse proxy)                                       │
│  ● Redis (cache + queue)                                       │
│  ● Supervisor (workers + scheduler)                            │
│  ● S3-compatible storage (for file attachments)                │
└────────────────────────────────────────────────────────────────┘
```

## Module Architecture

### Module 1: Orders & Production
```
Sales Order (ERPNext Standard)
  ├── Custom Fields (kvh_ops):
  │     kvh_production_status, kvh_payment_status,
  │     kvh_finish_type, include_installation,
  │     committed_delivery_date, branch,
  │     override_approved_by, cancellation_reason
  ├── Hook (kvh_ops/overrides/sales_order.py):
  │     validate → payment gate enforcement
  │     on_submit → create KVH Job Cards
  │     on_cancel → record cancellation
  └── Child: Sales Order Item (extended)
        Custom Fields: designer_assigned_to, fabricator_name_text,
                       design_status, factory_stage, sheet_spec,
                       grill_spec, installation_method

KVH Job Card (Custom DocType)
  ├── Links: Sales Order, User (designer), KVH Fabricator
  ├── States: factory_stage (12 stages), design_status (4 states)
  ├── Controller: check_order_completion → auto-advance SO status
  └── Triggers: log_stage_event on every stage change

KVH Stage Event (Custom DocType)
  └── Audit trail for every stage transition

KVH Rework (Custom DocType)
  └── Logged by Factory Supervisor per Job Card

KVH Order Edit Request (Custom DocType)
  └── CRE → Admin/Sales_Head approval workflow

KVH Internal Edit Request (Custom DocType)
  └── Production team edit approval workflow
```

### Module 2: Procurement
```
Supplier (ERPNext Standard, extended)
  Custom Fields: on_time_pct, opening_balance

Material Request (ERPNext Standard) ← Purchase Requisition
Request for Quotation (ERPNext Standard) ← RFQ
  └── Supplier Quotation (Standard) ← RFQ Quotation responses

Purchase Order (ERPNext Standard, extended)
  Custom Fields: kvh_po_status, kvh_mrn_number, kvh_payment_status
  Hook (kvh_ops/overrides/purchase_order.py):
    on_update_after_submit → MRN generation + stock inward

Stock Entry (ERPNext Standard) ← Material Transactions
  Types: Material Receipt (Inward), Material Issue, Material Transfer

Item (ERPNext Standard, extended)
  Custom Fields: kvh_category, min_stock_level, branch

Stock Reconciliation (ERPNext Standard) ← Stock Audits
Asset (ERPNext Standard) ← Machinery Register
Asset Maintenance Log (ERPNext Standard) ← Machinery Repairs
```

### Module 3: Leads & CRM
```
CRM Lead (FCRM Standard, extended)
  Custom Fields: lead_number, phone_norm, is_duplicate, merged_into,
                 ai_summary, location_lat/lng/url, converted_order,
                 next_followup_at, last_contacted_at, place, branch
  Hook (kvh_ops/overrides/crm_lead.py):
    before_insert → generate number, normalize phone, detect duplicate, auto-assign
    on_update → log stage/owner changes

CRM Stage (FCRM Standard) ← lead_stages
CRM Call Log (FCRM Standard) ← lead_calls
CRM Appointment / ToDo ← lead_followups
Assignment Rule ← lead auto-assignment round-robin
```

### Module 4: Fabricators & Payouts
```
KVH Fabricator (Custom DocType)  ← fabricators table
KVH Fabricator Rate Card (Custom DocType)  ← fabricator_rate_card table
KVH Fabricator Payout (Custom DocType)  ← fabricator_payout_runs
  ├── Child: KVH Fabricator Payout Item  ← fabricator_payout_lines
  ├── Status Workflow: Draft → Approved → Paid → Cancelled
  ├── Lock Guard: Approved/Paid runs cannot be edited
  ├── Auto-calculate: totals from line items (qty × rate)
  └── Auto-populate: from completed Job Cards in period
```

### Module 5: Marketing
```
KVH Marketing Client (Custom DocType)  ← marketing_clients
KVH Marketing Campaign (Custom DocType)  ← marketing_campaigns
KVH Marketing Content (Custom DocType)  ← marketing_content_items
KVH Marketing Ad (Custom DocType)  ← marketing_paid_ads
KVH Brand Asset (Custom DocType)  ← marketing_brand_assets
KVH Marketing Subscription (Custom DocType)  ← marketing_subscriptions
KVH Marketing Budget Entry (Custom DocType)  ← marketing_budget_entries
KVH Marketing SOP (Custom DocType)  ← marketing_sops
KVH Marketing Invoice (Custom DocType)  ← marketing_invoices
  ├── Child: KVH Marketing Invoice Item  ← marketing_invoice_items
  ├── Child: KVH Marketing Invoice Payment  ← marketing_invoice_payments
  ├── Auto-calculate GST: (subtotal - discount) × tax_percent / 100
  ├── Status auto-update: Sent → Partially Paid → Paid
  └── Public URL: /mkt-invoice/{token}  (no auth required)
KVH Marketing MIS Snapshot (Custom DocType)  ← marketing_mis_snapshots
  └── Child: KVH Marketing MIS Row  ← marketing_mis_salesperson_rows
```

### Module 6: Sales Management
```
KVH Sales Target (Custom DocType)  ← sm_targets
  └── Per-CRE, weekly/monthly targets with amount + leads + quotations

KVH Weekly Report (Custom DocType)  ← sm_weekly_reports
  └── CRE weekly submissions with auto_snapshot + overrides

KVH Customer Feedback (Custom DocType)  ← sm_feedback
  └── Rating 1-5, channel, category, follow-up tracking

KVH Daily Sales Log (Custom DocType)  ← daily activity logs
```

### Module 7: Incentives
```
KVH Incentive Rule (Custom DocType)  ← incentive_rules
  ├── effective_month (unique per month)
  └── Child: KVH Incentive Tier (replaces jsonb tiers[])
       Fields: from_amount, to_amount, incentive_amount

KVH Incentive Report (Script Report)
  └── Calculates per-CRE incentive based on monthly sales vs tiers
```

## Permission Architecture

### Role Hierarchy
```
KVH Admin (System Manager equivalent for KVH)
  └── Full access to all KVH DocTypes + settings

KVH Sales Head / KVH BDM
  └── All Sales Orders, Leads, Customers
  └── Approve Order Edit Requests
  └── Approve Payment Overrides
  └── View Sales MIS and reports

KVH CRE
  └── Own Sales Orders only
  └── Own Customers and Leads
  └── Request Order Edit Permission
  └── View own incentives and targets

KVH Production Head
  └── All Job Cards, Fabricator Payouts
  └── Approve Payout Runs
  └── View all factory stages

KVH Production Manager
  └── All Job Cards (read + write factory stage)
  └── View Payout Runs

KVH Factory Supervisor
  └── Assigned Job Cards (update factory stage)
  └── Log Reworks

KVH Design Team
  └── Assigned Job Cards (update design status)

KVH Store Keeper
  └── Inventory Items, Stock Entries, Stock Reconciliation
  └── Machinery Register

KVH Purchase Officer
  └── Material Request, RFQ, Purchase Order
  └── Supplier management

KVH Marketing Head
  └── All Marketing DocTypes
  └── Create/approve Marketing Invoices
  └── MIS snapshots

KVH Marketing Member
  └── Read access to marketing module
  └── Update assigned tasks and content items

KVH Operation Manager
  └── Cross-module read access (no write)
```

## Naming Series (mirrors KVH FY-scoped IDs)

| ERPNext Series | Format | Old System |
|---|---|---|
| Sales Order | KVH/OR/.FY./.#### | KVH/OR/26-27/0042 |
| Purchase Order | KVH/PO/.FY./.#### | KVH/PO/26-27/0018 |
| Material Request | KVH/MRN/.FY./.#### | KVH/MRN/26-27/0005 |
| Issue (Service Desk) | KVH/TKT/.FY./.#### | KVH/TKT/26-27/0003 |
| CRM Lead | KVH/LEAD/.FY./.#### | KVH/LEAD/26-27/0201 |
| KVH Marketing Campaign | KVH/MC/.FY./.#### | KVH/MC/26-27/0015 |
| KVH Marketing Invoice | KVH/MINV/.FY./.#### | KVH/MINV/26-27/0008 |
| KVH Fabricator Payout | KVH/FPR/.FY./.#### | KVH/FPR/26-27/0004 |
| KVH Job Card | KVH/JC/.FY./.#### | (new) |
| KVH Rework | KVH/RWK/.FY./.#### | (new) |
| Customer | KVH/CUS/.FY./.#### | KVH/CUS/26-27/0150 |

## Business Logic Migration Map

| Original Trigger | Table | Frappe Equivalent |
|---|---|---|
| `handle_new_user` | auth.users | `User.after_insert` hook (auto-create Employee) |
| `enforce_payment_gate` | orders | `sales_order.validate()` in overrides |
| `auto_advance_order_status` | order_items | `KVHJobCard.check_order_completion()` |
| `auto_inward_po` | purchase_orders | `purchase_order.on_update_after_submit()` |
| `apply_material_txn` | material_transactions | ERPNext Stock Ledger (automatic) |
| `recalc_po_payment` | po_payments | `purchase_order._recalculate_payment_status()` |
| `sync_machine_status` | machinery_repairs | `Asset Maintenance Log.on_update()` |
| `recalc_payout_run` | fabricator_payout_lines | `KVHFabricatorPayout._recalculate_totals()` |
| `guard_payout_line_lock` | fabricator_payout_lines | `KVHFabricatorPayout._validate_lock_guard()` |
| `sync_marketing_approval` | marketing_approvals | Frappe Workflow state transition |
| `recalc_marketing_invoice` | marketing_invoice_items/payments | `KVHMarketingInvoice._recalculate()` |
| `leads_before_insupd` | leads | `crm_lead.before_insert/before_save()` |
| `leads_auto_assign` | leads | `crm_lead._auto_assign()` |
| `log_lead_stage_change` | leads | `crm_lead.on_update()` |
| `lead_call_bump_contact` | lead_calls | `crm_lead.log_call()` |
| `lead_followup_sync` | lead_followups | `crm_lead._sync_next_followup()` |
| `log_stage_events` | order_items | `KVHJobCard.log_stage_event()` |
| `notify_order_cancelled` | orders | `sales_order.on_cancel()` |
| `notify_edit_request_created` | order_edit_requests | `KVHOrderEditRequest.after_insert()` |
| `notify_edit_request_decided` | order_edit_requests | `KVHOrderEditRequest.on_update()` |
| `set_updated_at` | all tables | Frappe auto-handles `modified` field |
| `assign_mrn_number` | purchase_orders | `purchase_order._generate_mrn_number()` |
| `assign_ticket_number` | service_tickets | Naming Series on Issue doctype |
