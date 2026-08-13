"""
KVH Incentive Report
====================
Calculates per-CRE incentive for a given month based on:
1. Their total sales (Sales Orders submitted in that month)
2. The active incentive rule for that month
3. The matching tier in the rule

Mirrors the incentives.tsx (35KB) calculation in the Lovable system.
"""

import frappe
from frappe import _
from frappe.utils import getdate, flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("CRE"),
            "fieldname": "cre_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 200,
        },
        {
            "label": _("CRE Name"),
            "fieldname": "cre_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Total Sales (₹)"),
            "fieldname": "total_sales",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Incentive Rule"),
            "fieldname": "rule_month",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": _("Tier"),
            "fieldname": "tier_label",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Incentive Amount (₹)"),
            "fieldname": "incentive_amount",
            "fieldtype": "Currency",
            "width": 170,
            "bold": 1,
        },
    ]


def get_data(filters):
    month_start = filters.get("month_start")
    month_end = filters.get("month_end")
    cre_filter = filters.get("cre_user")

    if not month_start or not month_end:
        frappe.throw(_("Please set Month Start and Month End filters"))

    # Get all CRE users
    cre_roles = frappe.get_all(
        "Has Role",
        filters={"role": "KVH CRE", "parenttype": "User"},
        fields=["parent"],
        distinct=True,
    )
    cre_users = [r.parent for r in cre_roles]

    if cre_filter:
        cre_users = [cre_filter] if cre_filter in cre_users else []

    if not cre_users:
        return []

    # Get total sales per CRE for the period
    sales_by_cre = frappe.db.sql(
        """
        SELECT
            so.owner as cre_user,
            SUM(so.grand_total) as total_sales
        FROM `tabSales Order` so
        WHERE so.transaction_date BETWEEN %s AND %s
          AND so.docstatus = 1
          AND so.owner IN ({placeholders})
        GROUP BY so.owner
        """.format(placeholders=", ".join(["%s"] * len(cre_users))),
        [month_start, month_end] + cre_users,
        as_dict=True,
    )

    sales_map = {row.cre_user: flt(row.total_sales) for row in sales_by_cre}

    # Find the incentive rule for this month
    rule_month = getdate(month_start).replace(day=1)
    rule = frappe.db.get_value(
        "KVH Incentive Rule",
        {"effective_month": rule_month},
        ["name", "effective_month"],
        as_dict=True,
    )

    tiers = []
    if rule:
        tiers = frappe.get_all(
            "KVH Incentive Tier",
            filters={"parent": rule.name},
            fields=["from_amount", "to_amount", "incentive_amount", "label"],
            order_by="from_amount asc",
        )

    data = []
    for cre in cre_users:
        total_sales = sales_map.get(cre, 0.0)
        cre_name = frappe.db.get_value("User", cre, "full_name") or cre

        incentive_amount = 0.0
        tier_label = "No tier matched"
        rule_month_str = str(rule_month) if rule else "No rule"

        # Find matching tier
        for tier in tiers:
            if flt(tier.from_amount) <= total_sales <= flt(tier.to_amount):
                incentive_amount = flt(tier.incentive_amount)
                tier_label = tier.label or f"₹{tier.from_amount:,.0f} – ₹{tier.to_amount:,.0f}"
                break

        data.append({
            "cre_user": cre,
            "cre_name": cre_name,
            "total_sales": total_sales,
            "rule_month": rule_month_str,
            "tier_label": tier_label,
            "incentive_amount": incentive_amount,
        })

    # Sort by total_sales descending
    data.sort(key=lambda x: x["total_sales"], reverse=True)
    return data
