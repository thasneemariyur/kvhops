# KVH Operations — ERPNext Installation Guide

## Prerequisites

### Server Requirements
| Component | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB SSD | 200 GB SSD |
| Python | 3.11+ | 3.11+ |
| Node.js | 18+ | 20 LTS |
| MariaDB | 10.6+ | 10.11 |
| Redis | 6+ | 7 |
| Nginx | 1.18+ | Latest |

### Domain & SSL
- Point a domain/subdomain to your server IP
- SSL certificate (Let's Encrypt recommended)

---

## Step 1: Install ERPNext using Frappe Bench

```bash
# Install system dependencies
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python3-dev python3-pip python3-setuptools \
    python3-venv python3.11 libffi-dev libssl-dev libmariadb-dev \
    mariadb-server redis-server nodejs npm nginx supervisor wkhtmltopdf

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install frappe-bench
pip3 install frappe-bench

# Create new bench (production setup)
bench init --frappe-branch version-15 /home/frappe/kvh-bench
cd /home/frappe/kvh-bench

# Create new site
bench new-site kvh.yourdomain.com \
    --mariadb-root-password <DB_ROOT_PASS> \
    --admin-password <ADMIN_PASS> \
    --db-name kvh_erpnext

# Install ERPNext
bench get-app erpnext --branch version-15
bench --site kvh.yourdomain.com install-app erpnext

# Install FCRM (Frappe CRM - provides CRM Lead, Campaign)
bench get-app crm
bench --site kvh.yourdomain.com install-app crm
```

## Step 2: Install kvh_ops App

```bash
cd /home/frappe/kvh-bench

# Option A: From local directory (copy the kvh_erpnext folder here)
# Copy c:\Users\muham\Desktop\OS\kvh_erpnext\kvh_ops to the server
# then:
bench get-app kvh_ops /path/to/kvh_ops

# Option B: Install from Git repo (after pushing to GitHub)
bench get-app kvh_ops https://github.com/your-org/kvh_ops.git --branch main

# Install the app on the site
bench --site kvh.yourdomain.com install-app kvh_ops
```

## Step 3: Configure ERPNext Setup Wizard

1. Open `https://kvh.yourdomain.com` in browser
2. Complete Setup Wizard:
   - **Company Name**: KVH Industries
   - **Company Abbreviation**: KVH
   - **Country**: India
   - **Currency**: INR
   - **Fiscal Year**: April → March (Indian FY)
   - **Chart of Accounts**: Indian Standard (GST-compliant)

## Step 4: Configure KVH-Specific Settings

### 4.1 Naming Series
Go to **Settings → Naming Series** and verify:
```
Sales Order:        KVH/OR/.FY./.####
Purchase Order:     KVH/PO/.FY./.####
Material Request:   KVH/MRN/.FY./.####
Issue:              KVH/TKT/.FY./.####
```

### 4.2 Branches
Go to **Setup → Company → Branches** and add:
- Main Branch (or specific branches per your setup)

### 4.3 Warehouses
Create warehouses for each branch:
- **Main Store** (parent: All Warehouses)
- **Production Floor** (parent: All Warehouses)

### 4.4 Item Groups
Ensure these Item Groups exist:
- Raw Material
- Consumable
- Fixed Asset
- Spare Parts

### 4.5 GST Configuration
Go to **Accounts → GST Settings**:
- Enter company GSTIN
- Configure HSN codes for your products
- Set up CGST/SGST/IGST accounts

### 4.6 Email Configuration
Go to **Settings → Email Domain**:
- Configure outbound email (for notifications)

### 4.7 AI Settings (for Lead Summary)
Go to **KVH Settings**:
- Enter OpenAI API Key
- Set API Base URL (or use default https://api.openai.com/v1)
- Set Model (default: gpt-4o-mini)

## Step 5: Create Custom Fields

```bash
bench --site kvh.yourdomain.com execute kvh_ops.fixtures.custom_fields.create_all_custom_fields
```

## Step 6: Load Fixtures

```bash
# Load KVH roles, feature flags, and default data
bench --site kvh.yourdomain.com execute kvh_ops.install.after_install
```

## Step 7: Set Up Production Environment

```bash
# Configure Nginx
sudo bench setup nginx
sudo service nginx restart

# Set up Supervisor (process manager)
sudo bench setup supervisor
sudo service supervisor restart

# Enable auto-start
sudo bench setup systemd
sudo systemctl enable kvh-bench.target
sudo systemctl start kvh-bench.target

# Set up Let's Encrypt SSL
sudo -H bench setup lets-encrypt kvh.yourdomain.com
```

## Step 8: Data Migration

### 8.1 Export data from Supabase
```sql
-- Run these queries in Supabase SQL editor and export as JSON

-- profiles
SELECT id, email, full_name, role, roles, branch, active FROM public.profiles;

-- clients
SELECT id, name, phone, email, district FROM public.clients;

-- vendors  
SELECT id, name, gst, email, phone, address, on_time_pct, opening_balance FROM public.vendors;

-- inventory_items
SELECT sku, item_name, category, unit_of_measurement, current_stock, min_stock_level, branch FROM public.inventory_items;

-- fabricators
SELECT id, name, active FROM public.fabricators;

-- fabricator_rate_card
SELECT product_key, display_name, rate, active FROM public.fabricator_rate_card;

-- leads
SELECT id, lead_number, name, phone, phone_norm, email, source, stage_key,
       owner_id, branch, place, notes, is_duplicate, ai_summary,
       last_contacted_at, next_followup_at FROM public.leads;

-- orders
SELECT order_id, customer_name, sales_person_id, amount, ordered_date,
       committed_delivery_date, branch, status, finish_type, include_installation,
       cancellation_reason FROM public.orders;

-- order_items
SELECT item_id, order_id, product_description, quantity, sheet_spec, grill_spec,
       installation_method, design_status, factory_stage,
       designer_assigned_to, fabricator_assigned_to, fabricator_name FROM public.order_items;
```

### 8.2 Run Migration
```bash
# Save exported JSON to /tmp/kvh_data.json
# Then run migration:
bench --site kvh.yourdomain.com execute kvh_ops.migration.migrate.run_full_migration \
    --kwargs '{"data": <contents of kvh_data.json>}'

# Or run phase by phase:
bench --site kvh.yourdomain.com execute kvh_ops.migration.migrate.migrate_users \
    --kwargs '{"profiles_data": [...]}'
```

## Step 9: User Setup

1. Go to **Settings → Users**
2. For each migrated user, send password reset email
3. Assign roles if not auto-assigned by migration
4. Enable/disable users as needed

## Step 10: Verification Checklist

Run these checks after installation:

- [ ] All 13 KVH roles appear in **Settings → Role List**
- [ ] Sales Order form shows KVH custom fields (Production Status, Finish Type, etc.)
- [ ] CRM Lead form shows KVH custom fields (Lead Number, Phone Norm, AI Summary, etc.)
- [ ] KVH Job Card list view shows data
- [ ] Naming series generates KVH/OR/YY-YY/NNNN format
- [ ] Feature flags exist in KVH Feature Flag doctype
- [ ] Fabricators and rate cards are populated
- [ ] Scheduler is running (check `bench --site kvh.yourdomain.com doctor`)
- [ ] Notifications arrive in Notification Log
- [ ] PDF Print Formats render correctly

---

## Upgrade Path

```bash
# To upgrade kvh_ops app:
cd /home/frappe/kvh-bench
bench update --pull
bench --site kvh.yourdomain.com migrate
bench build

# To upgrade ERPNext:
bench update --apps erpnext
bench --site kvh.yourdomain.com migrate
```

---

## Troubleshooting

### Scheduler not running
```bash
bench --site kvh.yourdomain.com doctor
sudo supervisorctl restart all
```

### Custom fields not appearing
```bash
bench --site kvh.yourdomain.com migrate
bench build --app kvh_ops
```

### Permission errors
```bash
bench --site kvh.yourdomain.com clear-cache
bench --site kvh.yourdomain.com clear-website-cache
```

### Migration errors
Check the migration log:
```bash
bench --site kvh.yourdomain.com console
# In console:
frappe.get_all("Error Log", filters={"method": ("like", "%kvh_ops.migration%")}, fields=["error"])
```
