# KVH Operations — ERPNext User Guide

## Getting Started

### Logging In
1. Go to `https://kvh.yourdomain.com`
2. Enter your email and password (provided by Admin)
3. On first login, change your password via **My Settings → Change Password**
4. Set up your profile photo and contact details

### Interface Overview
The ERPNext Desk has three main sections:
- **Top Navigation Bar** — Global search, notifications bell, user menu
- **Sidebar / Desk** — Module workspace shortcuts
- **Main Content Area** — Lists, forms, reports, dashboards

---

## MODULE GUIDES BY ROLE

---

## CRE (Customer Relationship Executive)

### Creating a Sales Order

1. Go to **Selling → Sales Order → New**
2. Fill in:
   - **Customer** — Type to search or create new
   - **Delivery Date** — Standard estimated delivery
   - **Committed Delivery Date** — The date promised to customer
   - **Finish Type** — Primer Finish or Powder Coating
   - **Include Installation** — Check if installation required
   - **Branch** — Your branch
3. In the **Items** table, add each product:
   - **Item Name / Description** — Product description (e.g. "Aluminium Sliding Window 4ft x 5ft")
   - **Qty** — Number of units
   - **Rate** — Price per unit
   - Fill **Sheet Spec**, **Grill Spec**, **Installation Method** as needed
4. Click **Save**

> [!IMPORTANT]
> **Payment Gate**: If advance payment < 35%, the order will be blocked at "Payment Pending" and cannot proceed to production. Collect at least 35% advance and record it, or request a payment override from your Sales Head.

### Recording Advance Payment
1. After saving the order, go to **Accounting → Payment Entry → New**
2. Set **Payment Type** = Receipt
3. Set **Party Type** = Customer, **Party** = customer name
4. Enter amount and set **Reference** = your Sales Order
5. Save and Submit

### Requesting Order Edit Permission
If you need to edit a submitted order:
1. Open the Sales Order
2. Click **Actions → Request Edit Permission**
3. Enter reason for edit
4. Wait for Sales Head / BDM / Admin to approve
5. Once approved, you will be notified and can edit within the allowed window

### Viewing Your Leads
Go to **CRM → Leads** — shows all leads assigned to you.

**Lead Quick Actions:**
- **Log Call** → Actions → Log Call → select direction/outcome
- **Add Follow-up** → Actions → Log Follow-up → set date/note
- **Generate AI Summary** → Actions → Generate AI Summary
- **Convert to Order** → Once lead is qualified, create Sales Order from the lead

### Checking Your Targets
Go to **KVH Ops → KVH Sales Target** → filter by your name and current month.

---

## Sales Head / BDM

### Approving Payment Overrides
1. Go to **Selling → Sales Orders** → filter by `kvh_payment_status = Payment Pending`
2. Open the order
3. Click **Actions → Approve Payment Override**
4. The order proceeds to "Pending Design"

### Approving Order Edit Requests
1. Go to **KVH Ops → KVH Order Edit Request** → filter by `Status = Pending`
2. Open the request
3. Review the reason
4. Click **Actions → Approve** or **Reject**
5. Set **Approved Until** duration (how long the CRE can edit)

### Sales MIS Dashboard
Go to **KVH Ops → Sales Reports → KVH Sales MIS**:
- Revenue by CRE (bar chart)
- Conversion funnel (leads → orders)
- Daily activity summary
- Target vs Actual comparison

### Managing Weekly Reports
1. Go to **KVH Ops → KVH Weekly Report**
2. Filter by week / CRE
3. Review key learnings and escalations
4. Mark as "Presented" after review meeting

---

## Production Team

### Factory Supervisor: Updating Job Card Stages

1. Go to **KVH Ops → KVH Job Card** → filter by your assigned fabricator or branch
2. Open a Job Card
3. Click **Actions → Update Factory Stage**
4. Select the new stage (e.g. CNC → Fabrication)
5. Add optional notes
6. Click **Update Stage**

**Stage Progression:**
```
Pending → CNC → Fabrication → Surface Finishing →
Primer Coating → Powder Coating → PU Foam Filling →
Accessories → Packing → [Installation] → Ready → Dispatched
```

### Logging a Rework
1. Open the Job Card with the issue
2. Click **Actions → Log Rework**
3. Select the rework reason:
   - Wrong measurement
   - Surface defect
   - Damaged in transit
   - Customer change
   - Quality rejection
4. Describe the issue and submit

### Production Head: Approving Fabricator Payouts
1. Go to **KVH Ops → KVH Fabricator Payout** → filter by `Status = Draft`
2. Open payout run
3. Review lines — verify quantities and rates
4. Click **Actions → Approve**
5. Once payment is made, click **Actions → Mark Paid** with payment reference

---

## Design Team

### Viewing Assigned Items
1. Go to **KVH Ops → KVH Job Card**
2. Filter by `designer_assigned_to = [your name]`
3. Shows all items assigned to you for design

### Updating Design Status
1. Open the Job Card
2. Change **Design Status** field:
   - **Pending** → **In Progress** → when you start
   - **In Progress** → **Hold** → if blocked
   - **Hold** → **In Progress** → when unblocked
   - **In Progress** → **Completed** → when design is done
3. Save

### Submitting Design Logs
1. Go to **KVH Ops → KVH Design Log → New**
2. Set date, your name, drawn sqft, undrawn sqft
3. Save

---

## Store Keeper

### Viewing Current Stock
Go to **Stock → Stock Balance** report — shows current qty for all items.

### Issuing Materials to Production Floor
1. **Stock → Stock Entry → New**
2. Set **Stock Entry Type** = Material Issue
3. Add items with quantities from the **From Warehouse** (Main Store)
4. Set **To Warehouse** = Production Floor
5. Submit

### Stock Audit
1. **Stock → Stock Reconciliation → New**
2. Select warehouse and posting date
3. Click **Get Items** to load all items with system quantities
4. Enter physically counted quantities
5. Submit (this adjusts stock to match physical count)

### Raising a Purchase Requisition
1. **Buying → Material Request → New**
2. Set **Material Request Type** = Purchase
3. Add items needed with quantities and required date
4. Submit for Purchase Officer to process

---

## Purchase Officer

### Processing a Purchase Requisition
1. **Buying → Material Request** → open Approved PR
2. Click **Create → Request for Quotation**
3. Add vendor quotation responses
4. Select best vendor → **Create → Purchase Order**

### Managing Purchase Orders
Status flow: **Draft → Confirmed → MRN_Generated → Received → Cancelled**

1. Open Purchase Order
2. When goods arrive, change **KVH PO Status** to `MRN_Generated`
3. System auto-generates **MRN Number** and creates a Stock Entry (Material Receipt)
4. Record payment: **Actions → Create Payment Entry**

### Supplier Invoices
1. **Buying → Purchase Invoice → New**
2. Link to **Purchase Order**
3. Verify quantities and amounts (GST auto-calculated)
4. Submit when verified

---

## Marketing Team

### Creating a Campaign
1. **KVH Ops → KVH Marketing Campaign → New**
2. Fill campaign name, client, sub-team, dates, budget
3. Add **Content Items** in the child table:
   - Title, Content Type, Platform, Designer/Creator assigned
   - Content Status: Idea → Drafting → Designing → Review → Published
4. Add **Paid Ads** if applicable
5. Save

### Creating a Marketing Invoice
1. **KVH Ops → KVH Marketing Invoice → New**
2. Select **Client**
3. Set invoice date, due date, and billing period
4. Add **Invoice Items**:
   - Kind: Retainer / Ad Spend / Subscription / Service / Other
   - Quantity × Unit Price = Amount (auto-calculated)
5. GST is auto-calculated (default 18%)
6. Save → Status = **Draft**
7. Change to **Sent** when emailed to client
8. Record payments in **Payments** tab when received

### Sharing Invoice with Client
Each invoice has a **Public URL** (visible on the form). Share this link with the client — they can view the invoice without logging into ERPNext.

### Managing Subscriptions
1. **KVH Ops → KVH Marketing Subscription**
2. Add all vendor subscriptions with renewal dates
3. System alerts Marketing Head 7 days before renewal

---

## Admin

### Managing Users
1. **Setup → Users → New User**
2. Enter email, name, set enabled = Yes
3. Assign roles in the **Roles** tab (tick required KVH roles)
4. Click **Send Welcome Email**

### Managing Feature Flags
1. **KVH Ops → KVH Feature Flag**
2. Toggle **Enabled** on/off for:
   - `incentives_page` — Shows incentive calculation to CREs
   - `rework_flow` — Enables rework logging in production
   - `cnc_stage` — Adds CNC stage to factory pipeline
   - `installation_module` — Enables installation tracking

### System Settings
1. **Setup → System Settings**
   - Date/Time format
   - Currency
   - Email footer
   - Session expiry (default 6 hours)

### Role Permissions
1. **Setup → Role Permissions Manager**
2. Select DocType and Role
3. Adjust permissions (Create/Read/Write/Delete/Submit/Cancel)

### Configuring AI Summary
1. **KVH Ops → KVH Settings**
2. Enter **OpenAI API Key**
3. Set **API Base URL** (default: https://api.openai.com/v1)
4. Set **Model** (default: gpt-4o-mini)
5. Save

### Audit Log
All document changes are tracked in **Activity Log**:
- **Tools → Activity Log** → filter by document type or user

---

## Common Tasks

### Finding Any Record (Global Search)
Press `Ctrl+G` or click the search bar at the top → type any name, order number, or phone number.

### Exporting Data to Excel
In any list view:
1. Select records (tick checkboxes)
2. Click **Actions → Export**
3. Select fields and download as CSV/Excel

### Printing Documents
Open any document → click **Print** → select print format:
- Sales Order → **KVH Order Status** (customer copy)
- Sales Order → **KVH Job Card** (production copy)
- Sales Order → **KVH Delivery Challan**
- Purchase Order → **KVH Purchase Order**
- KVH Fabricator Payout → **KVH Payout Sheet**

### Notifications
Click the bell icon (🔔) in the top navigation to see all notifications.
Notifications are sent for:
- Order ready for delivery/installation
- Edit permission approved/rejected
- Order cancelled
- Marketing subscription renewal due
- Payout approved/paid

### Keyboard Shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl+G` | Global search |
| `Ctrl+S` | Save current form |
| `Alt+N` | New document |
| `Esc` | Close dialog |
| `F5` | Refresh list |
