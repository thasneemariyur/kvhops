# KVH Operations — ERPNext Migration

> Complete migration of the KVH Industries Operations Management System from Lovable (React + Supabase) to ERPNext 15 / Frappe 15.

---

## Quick Navigation

| Document | Description |
|---|---|
| [CURRENT_SYSTEM_FEATURE_INVENTORY.md](docs/CURRENT_SYSTEM_FEATURE_INVENTORY.md) | Complete feature analysis of the original Lovable system |
| [ERPNext_FEATURE_MAPPING.md](docs/ERPNext_FEATURE_MAPPING.md) | Every feature mapped to ERPNext DocType (Standard/Custom) |
| [DATA_MODEL_MAPPING.md](docs/DATA_MODEL_MAPPING.md) | Table-by-table, field-by-field data model mapping |
| [DATA_MIGRATION_PLAN.md](docs/DATA_MIGRATION_PLAN.md) | Phased migration plan with export scripts and cutover strategy |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture, trigger→hook map, permission model |
| [INSTALLATION.md](docs/INSTALLATION.md) | Step-by-step ERPNext installation guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment, Nginx, backups, monitoring |
| [FEATURE_PARITY_TESTING.md](docs/FEATURE_PARITY_TESTING.md) | Complete test plan to verify feature parity |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Role-based user guide for all staff |

---

## Application Structure

```

├── docs/                          ← All migration documentation
└── kvh_ops/                       ← Frappe app
    └── kvh_ops/
        ├── hooks.py               ← Document event hooks + scheduler
        ├── install.py             ← Post-install setup (roles, flags, naming)
        ├── doctype/               ← 40 custom DocTypes
        │   ├── kvh_job_card/          Production tracking (core)
        │   ├── kvh_fabricator_payout/ Fabricator payment runs
        │   ├── kvh_rework/            Factory rework logging
        │   ├── kvh_order_edit_request/ CRE edit workflow
        │   ├── kvh_marketing_invoice/ Marketing billing (with public URL)
        │   ├── kvh_marketing_campaign/ Campaign management
        │   ├── kvh_incentive_rule/    Monthly incentive tiers
        │   ├── kvh_feature_flag/      Feature toggles
        │   ├── kvh_stage_event/       Production audit trail
        │   └── ... 31 more
        ├── overrides/             ← Standard DocType overrides
        │   ├── sales_order.py         Payment gate, job card creation
        │   ├── crm_lead.py            Phone normalization, auto-assign, AI
        │   └── purchase_order.py      MRN generation, stock auto-inward
        ├── fixtures/
        │   └── custom_fields.py       Custom fields on standard DocTypes
        ├── utils/
        │   ├── naming.py              KVH/PREFIX/YY-YY/NNNN generator
        │   └── ai.py                  OpenAI lead summary integration
        ├── tasks/
        │   └── daily.py               Overdue alerts, SLA, renewals, expiry
        ├── migration/
        │   └── migrate.py             Data migration orchestrator (all phases)
        ├── report/
        │   └── kvh_incentive_report/  Monthly CRE incentive calculation
        └── workspace/
            └── kvh_ops/               KVH Ops workspace shortcuts
```

---

## What Was Migrated

### Business Logic Preserved (25 Triggers → Python Hooks)
| Original Trigger | Replaced By |
|---|---|
| `enforce_payment_gate` | `sales_order.validate()` — 35% advance gate |
| `auto_advance_order_status` | `KVHJobCard.check_order_completion()` |
| `auto_inward_po` | `purchase_order._create_stock_inward()` |
| `recalc_payout_run` | `KVHFabricatorPayout._recalculate_totals()` |
| `guard_payout_line_lock` | `KVHFabricatorPayout._validate_lock_guard()` |
| `recalc_marketing_invoice` | `KVHMarketingInvoice._recalculate()` |
| `leads_before_insupd` | `crm_lead.before_insert()` |
| `leads_auto_assign` | `crm_lead._auto_assign()` (round-robin) |
| `lead_call_bump_contact` | `crm_lead.log_call()` |
| `lead_followup_sync` | `crm_lead._sync_next_followup()` |
| `recalc_po_payment` | `purchase_order._recalculate_payment_status()` |
| + 14 more | All documented in ARCHITECTURE.md |

### Standard ERPNext Used (No Custom Code)
- Purchase Order, Material Request, RFQ, Supplier Quotation
- Purchase Invoice, Sales Invoice, Payment Entry
- Stock Entry, Stock Reconciliation, Stock Ledger
- Asset, Asset Maintenance Log
- Issue (Service Desk), Delivery Note
- Employee, Leave Application, Attendance
- Workflow, Notification, Assignment Rule, Activity Log

### Custom DocTypes Created (40 total)
All 40 custom DocTypes are defined with full field schemas, permissions, and controllers.

---

## Installation

See [INSTALLATION.md](docs/INSTALLATION.md) for the complete guide.

**Quick start:**
```bash
bench init /home/frappe/kvh-bench --frappe-branch version-15
cd /home/frappe/kvh-bench
bench new-site kvh.yourdomain.com
bench get-app erpnext --branch version-15
bench get-app crm
bench --site kvh.yourdomain.com install-app erpnext crm
bench get-app kvh_ops /path/to/kvh_ops
bench --site kvh.yourdomain.com install-app kvh_ops
```

---

## Data Migration

See [DATA_MIGRATION_PLAN.md](docs/DATA_MIGRATION_PLAN.md) for the complete plan.

```bash
# Run full migration from exported Supabase JSON
bench --site kvh.yourdomain.com execute \
  kvh_ops.migration.migrate.run_full_migration \
  --kwargs '{"data": <kvh_export.json contents>}'
```

---

## Feature Parity

All features from the Lovable system are preserved. See [FEATURE_PARITY_TESTING.md](docs/FEATURE_PARITY_TESTING.md) for the complete test checklist.

Key preserved features:
- ✅ Payment gate (35% advance or override)
- ✅ FY-scoped naming (KVH/OR/26-27/0042)
- ✅ 12-stage factory pipeline with audit trail
- ✅ Fabricator payout with lock guard and auto-populate
- ✅ Lead round-robin auto-assignment
- ✅ Phone normalization and duplicate detection
- ✅ Marketing invoice with GST and public token URL
- ✅ Incentive calculation with monthly tier rules
- ✅ Feature flags for conditional features
- ✅ SLA breach detection and daily alerts
- ✅ AI-powered lead summaries
