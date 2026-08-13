# KVH Operations — Feature Parity Testing Guide

## How to Use This Document
For each feature below, perform the listed test actions and mark:
- ✅ PASS — Feature works identically to Lovable system
- ❌ FAIL — Feature missing or broken (create a GitHub issue)
- ⚠️ PARTIAL — Feature works but with minor differences (document)

---

## MODULE 1: ORDERS & PRODUCTION

### 1.1 Sales Order Creation
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create new order | Sales → New Sales Order → fill customer, items, dates | Order created with KVH/OR/YY-YY/NNNN naming | |
| Payment gate blocks | Create order with 0 advance → try to submit | Error: "Payment Pending — collect 35% advance or get override" | |
| Payment gate passes | Create order with ≥35% advance paid → submit | Order submits, kvh_production_status = "Pending Design" | |
| Override approval | Admin clicks "Approve Payment Override" on pending order | kvh_production_status changes to "Pending Design" | |
| Auto Job Cards | Submit a Sales Order with 3 items | 3 KVH Job Cards created, each in "Pending" stage | |
| Finish type | Create order with "Powder Coating" finish | finish_type = "Powder Coating" visible on Job Card | |
| Include installation | Create order with installation checkbox | include_installation = 1, final stage becomes "Ready for Installation" | |
| Cancellation | Cancel order → prompted for reason | cancellation_reason required, salesperson notified | |
| FY naming | Create order in April 2027 | Order number is KVH/OR/27-28/NNNN | |

### 1.2 Order Edit Request (CRE Workflow)
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| CRE requests edit | CRE → submitted order → "Request Edit" → give reason | KVH Order Edit Request created, Admin notified | |
| Admin approves | Admin → Edit Request → Approve → set expiry | Status = "Approved", CRE notified with expiry time | |
| CRE edits | CRE opens order within expiry window | Order is editable | |
| Auto expiry | Wait for expiry → try to edit | Access denied: "Edit permission expired" | |
| Admin rejects | Admin → Edit Request → Reject + note | Status = "Rejected", CRE notified with reason | |

### 1.3 Factory Stage Tracking (Job Card)
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| View Job Cards | Production → KVH Job Card list | All cards visible with current stage | |
| Update stage | Open Job Card → Update Factory Stage → select "Fabrication" | Stage updated, stage_updated_at/by recorded | |
| Stage event log | Update stage → view Stage History | KVH Stage Event record created with in/out/completed | |
| Assign designer | Open Job Card → set designer_assigned_to | Assignment event logged | |
| Design status | Design Team → update design_status to "Completed" | design_completed_at auto-set | |
| Auto-advance order | Set all Job Cards of an order to "Ready" | Order kvh_production_status → "Ready for Delivery" | |
| Salesperson notification | Above test | Salesperson gets in-app notification | |
| Installation auto-advance | All cards "Ready" on order with installation | kvh_production_status → "Ready for Installation" | |

### 1.4 Rework
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Log rework | Factory Supervisor → Job Card → "Log Rework" | KVH Rework record created with reason + stage | |
| Rework reasons | Open rework dialog | 5 standard reasons available | |
| Resolve rework | Production → KVH Rework → update status to "Resolved" | resolved_at auto-set | |
| Rework list | Production → KVH Rework list | All reworks filterable by order/stage/status | |

---

## MODULE 2: PROCUREMENT

### 2.1 Purchase Requisition (Material Request)
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create PR | Buying → Material Request → New | Created with items and requester | |
| Approve PR | Change status to "Approved" | Status updates | |
| PR → PO | Material Request → Create Purchase Order | PO linked to MR | |

### 2.2 Purchase Order
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create PO | Buying → Purchase Order → New | Created with KVH/PO/YY-YY/NNNN | |
| MRN generation | Change kvh_po_status to "MRN_Generated" | kvh_mrn_number = KVH/MRN/YY-YY/NNNN | |
| Auto stock inward | MRN_Generated → check Stock Entry | Stock Entry "Material Receipt" auto-created | |
| PO payment status | Add payment entry for PO | kvh_payment_status updates: Pending → Partial → Paid | |

### 2.3 RFQ
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create RFQ | Buying → Request for Quotation → New | RFQ created | |
| Add vendors | Add multiple suppliers to RFQ | Suppliers added | |
| Record quotes | Add Supplier Quotation | Prices recorded per vendor | |
| Compare quotes | View Supplier Quotations for RFQ | Can compare prices | |

### 2.4 Inventory
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| View stock | Stock → Items → check current_stock | Stock levels accurate post-migration | |
| Min stock alert | Item with min_stock_level → stock falls below | System shows reorder alert | |
| Stock ledger | Stock → Stock Ledger | All transactions visible | |

---

## MODULE 3: LEADS & CRM

### 3.1 Lead Management
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create lead | CRM → New Lead | Lead created with KVH/LEAD/YY-YY/NNNN | |
| Phone normalization | Enter phone "+91 98765 43210" | phone_norm = "9876543210" | |
| Duplicate detection | Create lead with same 10-digit phone | is_duplicate = 1 flag set | |
| Auto-assign | Create lead without owner | lead_owner auto-set via round-robin | |
| Stage change | Move lead to next stage | CRM Note logged with stage_change | |
| Log call | Lead → Log Call → select outcome | CRM Call Log created, last_contacted_at updated | |
| Log follow-up | Lead → Log Follow-up → set date | CRM Appointment created, next_followup_at updated | |
| AI summary | Lead → Generate AI Summary | ai_summary populated from OpenAI | |
| Merge leads | Admin → Merge lead A into lead B | merged_into set, duplicate lead closed | |

---

## MODULE 4: FABRICATORS & PAYOUTS

### 4.1 Fabricator Rate Card
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| View rate card | Production → KVH Fabricator Rate Card | All product rates visible | |
| Add rate | Create new rate card entry | product_key normalized (lowercase) | |
| Edit rate | Modify rate for product | Rate updates, payout recalculates | |

### 4.2 Fabricator Payout
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create payout | Production → KVH Fabricator Payout → New | Draft payout created with KVH/FPR/YY-YY/NNNN | |
| Auto-populate | Click "Auto-populate Lines" | Completed Job Cards in period added as lines | |
| Rate lookup | Auto-populated lines | Rate filled from rate card by product_key | |
| Amount calculation | Line with qty=3, rate=500 | amount = 1500 auto-calculated | |
| Recalculate | Add/remove lines | total_items, total_qty, total_amount update | |
| Approve payout | Production Head → Approve | Status = "Approved", approved_by set | |
| Lock guard | Try to edit lines on Approved payout | Error: "Cannot modify — payout is Approved" | |
| Mark paid | Approved → Mark Paid + reference | Status = "Paid", paid_at set | |

---

## MODULE 5: MARKETING

### 5.1 Marketing Invoice
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create invoice | Marketing → KVH Marketing Invoice → New | Invoice with KVH/MINV/YY-YY/NNNN | |
| Add items | Add invoice items with qty and rate | amount = qty × unit_price auto-calculated | |
| GST calculation | Set tax_percent = 18 | tax_amount = (subtotal - discount) × 18% | |
| Total calculation | Verify | total = (subtotal - discount) + tax_amount | |
| Record payment | Add payment in Payments tab | amount_paid updates, balance recalculates | |
| Status auto-update | Payment covers full total | Status changes: "Sent" → "Partially Paid" → "Paid" | |
| Public URL | Generate token | /mkt-invoice/{token} URL accessible without login | |
| Public view | Open public URL | Invoice details visible (no auth required) | |

### 5.2 Marketing Campaign
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create campaign | Marketing → KVH Marketing Campaign → New | Campaign created with KVH/MC/YY-YY/NNNN | |
| Add content | Campaign → Add KVH Marketing Content | Content linked to campaign | |
| Content workflow | Update content_status through stages | Stages: Idea → Drafting → Designing → Review → Published | |
| Campaign approval | Create approval workflow | Approval notification sent to approver | |

---

## MODULE 6: INCENTIVES

### 6.1 Incentive Rules
| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Create rule | KVH Incentive Rule → New → set effective_month | Rule created | |
| Add tiers | Add multiple tiers with ranges | Tier from_amount < to_amount validation | |
| Incentive report | Run KVH Incentive Report → select month | Per-CRE incentive calculated based on sales vs tiers | |

---

## MODULE 7: FEATURE FLAGS

| Test | Steps | Expected Result | Status |
|---|---|---|---|
| View flags | Admin → KVH Feature Flag list | 4 flags visible: incentives_page, rework_flow, cnc_stage, installation_module | |
| Disable flag | Set rework_flow = 0 | Rework options hidden from production UI | |
| Enable flag | Set rework_flow = 1 | Rework options visible | |

---

## MODULE 8: NOTIFICATIONS

| Test | Steps | Expected Result | Status |
|---|---|---|---|
| Order cancelled | Cancel a Sales Order | Salesperson gets notification in Notification Log | |
| Edit request created | CRE submits edit request | Admin/Sales_Head/BDM get notifications | |
| Edit request decided | Admin approves/rejects | CRE gets notification with decision + expiry | |
| Order ready | All Job Cards complete | Salesperson gets "Ready for Delivery" notification | |
| Subscription renewal | Marketing subscription due in <7 days | Marketing Head gets alert | |

---

## MODULE 9: NUMBER SERIES / NAMING

| Test | Steps | Expected Result | Status |
|---|---|---|---|
| FY boundary | Create order on March 31 | KVH/OR/25-26/NNNN (previous FY) | |
| FY boundary | Create order on April 1 | KVH/OR/26-27/NNNN (new FY) | |
| Sequential | Create 3 orders | NNNN is sequential: 0001, 0002, 0003 | |
| Parallel safe | Create orders simultaneously | No duplicate numbers | |

---

## REGRESSION: MIGRATED DATA

| Check | Query | Expected |
|---|---|---|
| User count | Users in Frappe | = count of active profiles in Supabase |
| Order count | Sales Orders | = count of orders in Supabase (excluding cancelled) |
| Lead count | CRM Leads | = count of leads in Supabase |
| Item count | Items | = count of inventory_items in Supabase |
| Vendor count | Suppliers | = count of vendors in Supabase |
| Fabricator count | KVH Fabricators | = count of fabricators in Supabase |
| Rate card count | KVH Fabricator Rate Cards | = count of active rate_card rows |
| Job Cards | KVH Job Cards | Exist for all submitted orders |
