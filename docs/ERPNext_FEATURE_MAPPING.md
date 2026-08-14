# KVH Operations — ERPNext Feature Mapping

## Legend
- **Standard** — Uses ERPNext/Frappe DocType with no modification
- **Standard+Custom** — Uses standard DocType with custom fields added
- **Custom** — New DocType created in kvh_ops app

---

## MODULE 1: ORDERS & PRODUCTION

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Sales Order | `orders` table | Sales Order | Standard+Custom | `overrides/sales_order.py` |
| Order Items | `order_items` table | Sales Order Item (child) | Standard+Custom | Custom fields fixture |
| Payment Gate (35%) | `enforce_payment_gate` trigger | Sales Order `validate()` hook | Custom | `sales_order.validate()` |
| Payment Status | `payment_status` enum | `kvh_payment_status` custom field | Custom | `sales_order._compute_payment_status()` |
| Override Approval | `override_approved_by` field | `override_approved_by` custom field | Custom | `sales_order.approve_payment_override()` |
| Production Status | `order_status` enum | `kvh_production_status` custom field | Custom | `sales_order.py` |
| Finish Type | `finish_type` (Primer/Powder) | `kvh_finish_type` custom field | Custom | Custom field on Sales Order |
| Include Installation | `include_installation` flag | `include_installation` custom field | Custom | Custom field on Sales Order |
| Committed Delivery | `committed_delivery_date` | `committed_delivery_date` custom field | Custom | Custom field on Sales Order |
| Order Cancellation | `cancelled_at/by/reason` | Standard cancel + `cancellation_reason` field | Standard+Custom | `sales_order.on_cancel()` |
| Order Edit Request (CRE) | `order_edit_requests` table | KVH Order Edit Request | Custom | `doctype/kvh_order_edit_request/` |
| Internal Edit Request (Production) | `order_internal_edit_requests` | KVH Internal Edit Request | Custom | `doctype/kvh_internal_edit_request/` |
| Job Card (per item) | `order_items` with stage | KVH Job Card | Custom | `doctype/kvh_job_card/` |
| Designer Assignment | `designer_assigned_to` | Custom field on SO Item + KVH Job Card | Custom | Both |
| Fabricator Assignment | `fabricator_assigned_to/name` | Custom field on SO Item + KVH Job Card | Custom | Both |
| Design Status | `design_status` enum | Select field (Pending/In Progress/Hold/Completed) | Custom | KVH Job Card field |
| Factory Stage | `factory_stage` enum (12 stages) | Select field on KVH Job Card | Custom | KVH Job Card field |
| Stage Event Log | `order_item_stage_events` | KVH Stage Event | Custom | `doctype/kvh_stage_event/` |
| Auto-Advance Order | `auto_advance_order_status` trigger | `KVHJobCard.check_order_completion()` | Custom | `kvh_job_card.py` |
| Rework | `reworks` table | KVH Rework | Custom | `doctype/kvh_rework/` |
| Rework Reasons | `dropdown_options(rework_reasons)` | Select field options | Custom | Seeded in install.py |
| Design Log | `design_logs` table | KVH Design Log | Custom | `doctype/kvh_design_log/` |
| Delivery Management | `delivery.tsx` | Delivery Note | Standard | ERPNext standard |
| Delivery Challan PDF | `pdf_templates.dc` | Print Format | Standard | ERPNext Print Format |
| Job Card PDF | `pdf_templates.job_card` | Print Format | Custom | KVH Job Card Print Format |
| Order Status PDF | `pdf_templates.order_status` | Print Format | Custom | KVH Order Status Print Format |
| Invoice PDF | `pdf_templates.invoice` | Sales Invoice Print Format | Standard | ERPNext standard |
| Installation Module | `installation.tsx` | KVH Installation | Custom | `doctype/kvh_installation/` |
| Factory Checklist | `factory.checklists` | KVH Factory Checklist | Custom | `doctype/kvh_factory_checklist/` |
| Production MIS | `production-mis.tsx` | Script Report | Custom | `report/kvh_production_mis/` |
| CNC Stage Flag | `cnc_stage` feature flag | KVH Feature Flag | Custom | Toggle CNC in factory stage options |

---

## MODULE 2: PRE-SALES / LEAD MANAGEMENT

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Lead | `leads` table | CRM Lead (FCRM) | Standard+Custom | `overrides/crm_lead.py` |
| Lead Number | `lead_number` (KVH/LEAD/YY/NNNN) | `lead_number` custom field | Custom | `crm_lead.before_insert()` |
| Phone Normalization | `phone_norm` (last 10 digits) | `phone_norm` custom field | Custom | `crm_lead._normalize_phone()` |
| Duplicate Detection | `is_duplicate` + `phone_norm` check | `is_duplicate` custom field | Custom | `crm_lead._detect_duplicate()` |
| Lead Merge | `merged_into_id` field | `merged_into` link field | Custom | `crm_lead.merge_leads()` |
| Lead Stages | `lead_stages` table (configurable) | CRM Stage (FCRM) | Standard | FCRM standard |
| Auto-Assign Round-Robin | `leads_auto_assign` trigger | `crm_lead._auto_assign()` | Custom | Assignment via `crm_lead.py` |
| Lead Activities | `lead_activities` table | CRM Note | Standard+Custom | `crm_lead._log_activity()` |
| Lead Calls | `lead_calls` table | CRM Call Log | Standard+Custom | `crm_lead.log_call()` |
| last_contacted_at sync | `lead_call_bump_contact` trigger | `crm_lead.log_call()` side effect | Custom | `crm_lead.py` |
| Lead Follow-ups | `lead_followups` table | CRM Appointment / ToDo | Standard+Custom | `crm_lead.log_followup()` |
| next_followup_at sync | `lead_followup_sync` trigger | `crm_lead._sync_next_followup()` | Custom | `crm_lead.py` |
| Lead Images | `lead_images` table | File attachments | Standard | Frappe File |
| Lead Custom Fields | `lead_custom_fields` table | Custom Field (Frappe) | Standard | Frappe Custom Field |
| Lead Workflows | `lead_workflows` table | Assignment Rule | Standard+Custom | `doctype/kvh_lead_workflow/` |
| AI Summary | `ai_summary` field + AI SDK | `ai_summary` custom field + `utils/ai.py` | Custom | `crm_lead.generate_ai_summary()` |
| Location Fields | `location_lat/lng/url` | Custom fields on CRM Lead | Custom | Custom fields fixture |
| Converted Order | `converted_order_id` | `converted_order` link field | Custom | Custom fields fixture |

---

## MODULE 3: SALES MANAGEMENT

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| SM Teams | `sm_teams` table | Sales Team (ERPNext) | Standard+Custom | Extend with `branch` |
| SM Team Members | `sm_team_members` table | Sales Team member child | Standard | ERPNext standard |
| SM Customers | `sm_customers` table | Customer | Standard+Custom | Custom fields fixture |
| Customer Number | `customer_number` (KVH/CUS/YY/NNNN) | `customer_number_kvh` custom field | Custom | `crm_lead.py` side effect |
| Customer Feedback | `sm_feedback` table | KVH Customer Feedback | Custom | `doctype/kvh_customer_feedback/` |
| Sales Targets | `sm_targets` table | KVH Sales Target | Custom | `doctype/kvh_sales_target/` |
| Weekly Reports | `sm_weekly_reports` table | KVH Weekly Report | Custom | `doctype/kvh_weekly_report/` |
| Daily Logs | sales activity logs | KVH Daily Sales Log | Custom | `doctype/kvh_daily_sales_log/` |
| Sales MIS | `sales-mis.tsx` charts | Script Report | Custom | `report/kvh_sales_mis/` |
| Quotations | Quotation management | Quotation (ERPNext) | Standard | ERPNext standard |

---

## MODULE 4: PROCUREMENT & STORE

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Vendors | `vendors` table | Supplier | Standard+Custom | Custom fields fixture |
| Purchase Requisition | `purchase_requisitions` table | Material Request | Standard+Custom | ERPNext standard |
| PR Approval | `status: Draft→Approved` | Material Request workflow | Standard | ERPNext workflow |
| RFQ | `rfqs` table | Request for Quotation | Standard | ERPNext standard |
| RFQ Vendors | `rfq_vendors` table | RFQ Supplier (child) | Standard | ERPNext standard |
| RFQ Quotations | `rfq_quotations` table | Supplier Quotation | Standard | ERPNext standard |
| Purchase Order | `purchase_orders` table | Purchase Order | Standard+Custom | `overrides/purchase_order.py` |
| MRN Number | `mrn_number` field | `kvh_mrn_number` custom field | Custom | `purchase_order._generate_mrn_number()` |
| Auto Stock Inward | `auto_inward_po` trigger | `purchase_order._create_stock_inward()` | Custom | `overrides/purchase_order.py` |
| PO Payments | `po_payments` table | Payment Entry | Standard | ERPNext standard |
| Payment Status | `recalc_po_payment` trigger | `purchase_order._recalculate_payment_status()` | Custom | `overrides/purchase_order.py` |
| Supplier Invoice | `supplier_invoices` table | Purchase Invoice | Standard | ERPNext standard (GST auto) |
| Debit Notes | `debit_notes` table | Purchase Invoice (Return) | Standard | ERPNext standard |
| Material Transfers | `material_transfers` table | Stock Entry (Transfer) | Standard | ERPNext standard |
| Inventory Items | `inventory_items` table | Item | Standard+Custom | Custom fields fixture |
| Stock Transactions | `material_transactions` table | Stock Ledger Entry (auto) | Standard | ERPNext auto-creates |
| Transaction Types | Inward/Outward/Floor_Issue/etc. | Stock Entry Types | Standard | Map to ERPNext purposes |
| Stock Audits | `stock_audits` table | Stock Reconciliation | Standard | ERPNext standard |
| Machinery Register | `machinery_register` table | Asset | Standard+Custom | ERPNext Assets module |
| Machinery Repairs | `machinery_repairs` table | Asset Maintenance Log | Standard+Custom | ERPNext standard |
| Stock Ledger View | `store.ledger` route | Stock Ledger report | Standard | ERPNext standard |

---

## MODULE 5: FABRICATORS

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Fabricators Master | `fabricators` table | KVH Fabricator | Custom | `doctype/kvh_fabricator/` |
| Rate Card | `fabricator_rate_card` table | KVH Fabricator Rate Card | Custom | `doctype/kvh_fabricator_rate_card/` |
| product_key normalization | lowercase + collapse whitespace | `_normalize_product_key()` function | Custom | `kvh_fabricator_payout.py` |
| Payout Runs | `fabricator_payout_runs` table | KVH Fabricator Payout | Custom | `doctype/kvh_fabricator_payout/` |
| Payout Lines | `fabricator_payout_lines` table | KVH Fabricator Payout Item (child) | Custom | `doctype/kvh_fabricator_payout_item/` |
| Lock Guard | `guard_payout_line_lock` trigger | `KVHFabricatorPayout._validate_lock_guard()` | Custom | `kvh_fabricator_payout.py` |
| Auto Totals | `recalc_payout_run` trigger | `KVHFabricatorPayout._recalculate_totals()` | Custom | `kvh_fabricator_payout.py` |
| Auto-Populate | Auto mode from completed Job Cards | `KVHFabricatorPayout.auto_populate_lines()` | Custom | `kvh_fabricator_payout.py` |
| Approval Workflow | Draft→Approved→Paid | `KVHFabricatorPayout.approve()` + `mark_paid()` | Custom | `kvh_fabricator_payout.py` |
| Computation PDF | `pdf_templates.fabricator_computation` | Print Format | Custom | KVH Fabricator Computation Format |
| Payout PDF | `pdf_templates.fabricator_payout` | Print Format | Custom | KVH Fabricator Payout Format |

---

## MODULE 6: INCENTIVES

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Incentive Rules | `incentive_rules` table (jsonb tiers) | KVH Incentive Rule | Custom | `doctype/kvh_incentive_rule/` |
| Incentive Tiers | `tiers jsonb` array | KVH Incentive Tier (child table) | Custom | Child table of KVH Incentive Rule |
| Feature Flag | `incentives_page` flag | KVH Feature Flag | Custom | `KVH Feature Flag` doctype |
| Incentive Report | `incentives.tsx` (35KB) | Script Report | Custom | `report/kvh_incentive_report/` |

---

## MODULE 7: MARKETING

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Marketing Clients | `marketing_clients` table | KVH Marketing Client | Custom | `doctype/kvh_marketing_client/` |
| Campaigns | `marketing_campaigns` table | KVH Marketing Campaign | Custom | `doctype/kvh_marketing_campaign/` |
| Campaign ID | `KVH/MC/YY-YY/NNNN` | Naming Series | Custom | `kvh_ops/utils/naming.py` |
| Content Items | `marketing_content_items` table | KVH Marketing Content | Custom | `doctype/kvh_marketing_content/` |
| Paid Ads | `marketing_paid_ads` table | KVH Marketing Ad | Custom | `doctype/kvh_marketing_ad/` |
| Brand Assets | `marketing_brand_assets` table | KVH Brand Asset | Custom | `doctype/kvh_brand_asset/` |
| Subscriptions | `marketing_subscriptions` table | KVH Marketing Subscription | Custom | `doctype/kvh_marketing_subscription/` |
| Subscription Renewals | manual monitoring | Daily task alert | Custom | `tasks/daily.py` |
| Budget Entries | `marketing_budget_entries` table | KVH Marketing Budget Entry | Custom | `doctype/kvh_marketing_budget_entry/` |
| Marketing Tasks | `marketing_tasks` table | Task (ERPNext) | Standard+Custom | Extend Task doctype |
| Approvals | `marketing_approvals` table | Frappe Workflow | Standard | ERPNext Workflow engine |
| Campaign Status Sync | `sync_marketing_approval` trigger | Workflow state transition | Standard | ERPNext Workflow |
| SOPs | `marketing_sops` table | KVH Marketing SOP | Custom | `doctype/kvh_marketing_sop/` |
| Marketing Invoice | `marketing_invoices` table | KVH Marketing Invoice | Custom | `doctype/kvh_marketing_invoice/` |
| Invoice Number | `KVH/MINV/YY-YY/NNNN` | Naming Series | Custom | `kvh_ops/utils/naming.py` |
| Invoice Items | `marketing_invoice_items` table | KVH Marketing Invoice Item (child) | Custom | Child table |
| Invoice Payments | `marketing_invoice_payments` table | KVH Marketing Invoice Payment (child) | Custom | Child table |
| GST Calculation | `recalc_marketing_invoice` trigger | `KVHMarketingInvoice._recalculate()` | Custom | `kvh_marketing_invoice.py` |
| Status Auto-Update | `recalc_marketing_invoice` trigger | `KVHMarketingInvoice._recalculate()` | Custom | `kvh_marketing_invoice.py` |
| Public Invoice URL | `marketing-invoice.$token` route | Custom Frappe page (no auth) | Custom | `get_invoice_by_token()` whitelist |
| MIS Snapshots | `marketing_mis_snapshots` table | KVH Marketing MIS Snapshot | Custom | `doctype/kvh_marketing_mis_snapshot/` |
| MIS Rows | `marketing_mis_salesperson_rows` table | KVH Marketing MIS Row (child) | Custom | Child table |

---

## MODULE 8: HRMS

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Staff Management | `hrms.staff` module | Employee (ERPNext HR) | Standard | ERPNext HR module |
| Leave Management | HRMS module | Leave Application | Standard | ERPNext HR |
| Attendance | HRMS module | Attendance | Standard | ERPNext HR |
| Calendar | `hrms.calendar` | Leave + Event Calendar | Standard | ERPNext HR |
| Team Roster | `team-roster` route | ERPNext HR reports | Standard | ERPNext HR |

---

## MODULE 9: SERVICE DESK

| Feature | Lovable Implementation | ERPNext DocType | Type | kvh_ops Component |
|---|---|---|---|---|
| Service Tickets | `service_tickets` table | Issue (Support) | Standard+Custom | Add `ticket_number` field |
| Ticket Number | `KVH/TKT/YY-YY/NNNN` | Naming Series | Custom | Configure on Issue doctype |
| Ticket Status | status tracking | Issue status | Standard | ERPNext standard |

---

## MODULE 10: ACCOUNTS

| Feature | Lovable Implementation | ERPNext DocType | Type | Notes |
|---|---|---|---|---|
| Receipts | `ReceiptsCard` component | Payment Entry (Receipt type) | Standard | ERPNext Accounts |
| Refunds | `RefundsCard` component | Payment Entry (Refund type) | Standard | ERPNext Accounts |
| GST Accounting | CGST/SGST/IGST on invoices | Purchase/Sales Invoice GST | Standard | ERPNext GST auto-handles |

---

## MODULE 11: ADMIN

| Feature | Lovable Implementation | ERPNext DocType | Type | Notes |
|---|---|---|---|---|
| User Management | `profiles` table + admin panel | User | Standard | ERPNext standard |
| Role Management | `app_role` enum + `roles[]` | Role, Has Role | Standard | ERPNext standard |
| Branch Management | `branch` field on profiles | Branch | Standard | ERPNext standard |
| Feature Flags | `feature_flags` table | KVH Feature Flag | Custom | `doctype/kvh_feature_flag/` |
| Custom Fields | `custom_field_definitions/values` | Custom Field (Frappe) | Standard | Frappe's own Custom Field |
| Dropdown Options | `dropdown_options` table | Select field options | Standard | Frappe Customize Form |
| Document Templates | `document_templates` singleton | Letter Head | Standard | ERPNext Letter Head |
| PDF Templates | `pdf_templates` table | Print Format | Standard | ERPNext Print Format |
| Email Notifications | settings route | Notification | Standard | Frappe Notification |
| Audit Logs | `admin.settings.audit` | Activity Log | Standard | Frappe Activity Log |
| CSV Import | `admin.settings.import` | Data Import | Standard | ERPNext Data Import |
| Backup | `admin.settings.backup` | System Backups | Standard | ERPNext |
| SLA Management | `admin.sla.tsx` (21KB) | KVH SLA Rule + Daily Task | Custom | `doctype/kvh_sla_rule/` + `tasks/daily.py` |

---

## SYSTEM FEATURES

| Feature | Lovable Implementation | ERPNext Equivalent | Type | Notes |
|---|---|---|---|---|
| Naming Series | `next_fy_id()` PostgreSQL function | Frappe Naming Series | Standard+Custom | Custom `utils/naming.py` for exact format |
| Notifications | `notifications` table | Notification Log | Standard | Frappe built-in |
| Auth | Supabase Auth | Frappe Login | Standard | Email/password |
| Multi-Role | `roles[]` array | Has Role (multiple per user) | Standard | ERPNext native |
| Row-Level Security | Supabase RLS policies | Frappe Permissions | Standard | DocType-level |
| File Storage | Supabase Storage | Frappe File System / S3 | Standard | Configure S3 for scale |
| In-App Notifications | `NotificationsBell` component | Notification Log bell | Standard | ERPNext Desk |
| Global Search | `GlobalSearch` component | Frappe Global Search | Standard | ERPNext Desk |
| AI Integration | AI SDK + OpenAI | `utils/ai.py` + openai package | Custom | `openai` Python package |
| Public Token Pages | `marketing-invoice.$token` | Custom Frappe page | Custom | `get_invoice_by_token()` |

---

## ELIMINATED / REPLACED

| Lovable Feature | Replacement | Reason |
|---|---|---|
| `fy_sequences` table | ERPNext Naming Series | Native FY-scoped numbering |
| `number_series` table | ERPNext Naming Series config | Native naming config |
| `lead_assignment_state` table | Assignment Rule config | ERPNext Assignment Rules |
| Supabase RLS policies | Frappe Permission Engine | Role-based permissions |
| PostgreSQL triggers | Frappe hooks + controllers | Python-level business logic |
| TanStack Router | Frappe Desk Router | ERPNext native routing |
| Radix UI components | Frappe form builder | ERPNext form system |
| Recharts | ERPNext Dashboard Charts | Built-in charting |
| jsPDF client-side PDF | Frappe server-side PDF (wkhtmltopdf) | Server PDF generation |
