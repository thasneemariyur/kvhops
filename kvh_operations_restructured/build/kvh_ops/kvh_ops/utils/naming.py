"""
Utility module for KVH FY-scoped naming series.
Mirrors the next_fy_id() PostgreSQL function from the Lovable system.

Format: KVH/PREFIX/YY-YY/NNNN
Example: KVH/OR/26-27/0042
"""

import frappe
from frappe.utils import getdate, now_datetime
from datetime import date


def get_fy_code(d=None):
    """
    Get the Indian financial year code for a given date.
    Indian FY runs April 1 - March 31.
    e.g. date 2026-08-11 → '26-27'
         date 2026-02-15 → '25-26'
    Mirrors: fy_code() PostgreSQL function.
    """
    if d is None:
        d = date.today()
    elif isinstance(d, str):
        d = getdate(d)

    month = d.month
    year = d.year

    if month >= 4:
        # April onwards: FY is year/year+1
        fy_start = year % 100
        fy_end = (year + 1) % 100
    else:
        # Jan-Mar: FY is year-1/year
        fy_start = (year - 1) % 100
        fy_end = year % 100

    return f"{fy_start:02d}-{fy_end:02d}"


def next_fy_id(prefix, d=None):
    """
    Generate the next FY-scoped ID for a given prefix.
    Format: KVH/PREFIX/YY-YY/NNNN
    Thread-safe using FOR UPDATE on fy_sequences table.

    Mirrors: next_fy_id() PostgreSQL function.

    Args:
        prefix: Module prefix e.g. 'OR', 'PO', 'LEAD', 'MRN', 'TKT', 'MC', 'MINV', 'FPR', 'CUS'
        d: Date to use for FY calculation (defaults to today)

    Returns:
        str: e.g. 'KVH/OR/26-27/0042'
    """
    if d is None:
        d = date.today()
    elif isinstance(d, str):
        d = getdate(d)

    fy = get_fy_code(d)

    # Use frappe's built-in locking via db.sql with FOR UPDATE
    existing = frappe.db.sql(
        """
        SELECT last_value FROM `tabKVH FY Sequence`
        WHERE prefix = %s AND fy = %s
        FOR UPDATE
        """,
        (prefix, fy),
        as_dict=True,
    )

    if existing:
        last_value = existing[0].last_value + 1
        frappe.db.sql(
            "UPDATE `tabKVH FY Sequence` SET last_value = %s WHERE prefix = %s AND fy = %s",
            (last_value, prefix, fy),
        )
    else:
        last_value = 1
        frappe.db.sql(
            "INSERT INTO `tabKVH FY Sequence` (name, prefix, fy, last_value, creation, modified, modified_by, owner, docstatus) "
            "VALUES (%s, %s, %s, %s, NOW(), NOW(), %s, %s, 0)",
            (f"{prefix}-{fy}", prefix, fy, last_value, frappe.session.user, frappe.session.user),
        )

    return f"KVH/{prefix}/{fy}/{last_value:04d}"


# Prefix constants (matching number_series table from Lovable)
PREFIX_ORDER = "OR"
PREFIX_PO = "PO"
PREFIX_MRN = "MRN"
PREFIX_TICKET = "TKT"
PREFIX_LEAD = "LEAD"
PREFIX_CAMPAIGN = "MC"
PREFIX_MKT_INVOICE = "MINV"
PREFIX_FABRICATOR_PAYOUT = "FPR"
PREFIX_CUSTOMER = "CUS"
PREFIX_JOB_CARD = "JC"
PREFIX_REWORK = "RWK"
PREFIX_EDIT_REQUEST = "ER"
