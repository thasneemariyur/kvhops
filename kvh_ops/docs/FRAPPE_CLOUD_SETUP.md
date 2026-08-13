# KVH Ops, Frappe Cloud Setup

This repository is structured as a standard Frappe app:

```text
kvh_ops/
├── pyproject.toml
├── README.md
└── kvh_ops/
    ├── hooks.py
    ├── modules.txt
    ├── patches.txt
    ├── __init__.py
    ├── config/
    ├── doctype/
    ├── fixtures/
    ├── migration/
    ├── overrides/
    ├── report/
    ├── tasks/
    ├── utils/
    └── workspace/
```

In GitHub, the repository root must contain the `kvh_ops` directory shown above.
Do not upload the ZIP file itself as the app source.

Recommended branch for this codebase: `main`.

The app is targeted to Frappe/ERPNext version 15 and declares CRM as a required app because the code uses `CRM Lead` and `CRM Appointment`.

After adding the app to the Frappe Cloud bench, install ERPNext and Frappe CRM on the same bench before installing KVH Ops.
