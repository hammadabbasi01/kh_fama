# Copyright (c) 2025, Hammad
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    from_date = filters.get("from_date") or "2000-01-01"
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    # Get monthly data
    sales_data = get_sales_data(from_date, to_date)
    receipts_data = get_receipts_data(from_date, to_date)
    opening_balances = get_opening_balances(from_date)

    # ✅ Collect and sort months chronologically
    def month_sort_key(month_label):
        # Convert 'Aug 2025' → datetime(2025, 8, 1)
        try:
            return frappe.utils.get_datetime("01 " + month_label).date()
        except Exception:
            return frappe.utils.get_datetime("01 Jan 1900").date()

    months = sorted(
        list({row['month'] for row in sales_data + receipts_data}),
        key=month_sort_key
    )

    # Unique customers from all sources
    customers = sorted(
        list({
            *[row['customer'] for row in sales_data],
            *[row['customer'] for row in receipts_data],
            *opening_balances.keys()
        }),
        key=lambda x: x.lower() if x else ""
    )

    final_data = []

    for customer in customers:
        row = {
            "customer": customer,
            "opening": opening_balances.get(customer, 0),
            "customer_ledger": 0
        }

        # Initialize month columns
        for month in months:
            row[f"{month}_sales"] = 0
            row[f"{month}_receipts"] = 0

        # Fill monthly sales
        for s in sales_data:
            if s["customer"] == customer:
                row[f"{s['month']}_sales"] = s["sales"]

        # Fill monthly receipts
        for r in receipts_data:
            if r["customer"] == customer:
                row[f"{r['month']}_receipts"] = r["receipts"]

        # Calculate ledger (Opening + Total Sales − Total Receipts)
        total_sales = sum(row[f"{m}_sales"] for m in months)
        total_receipts = sum(row[f"{m}_receipts"] for m in months)
        row["customer_ledger"] = row["opening"] + total_sales - total_receipts

        final_data.append(row)

    # Add total row
    total_row = {"customer": "Total", "opening": 0, "customer_ledger": 0}
    for month in months:
        total_row[f"{month}_sales"] = 0
        total_row[f"{month}_receipts"] = 0

    for row in final_data:
        total_row["opening"] += row["opening"]
        total_row["customer_ledger"] += row["customer_ledger"]
        for month in months:
            total_row[f"{month}_sales"] += row[f"{month}_sales"]
            total_row[f"{month}_receipts"] += row[f"{month}_receipts"]

    final_data.append(total_row)

    # Columns
    columns = get_columns(months)

    return columns, final_data


def get_sales_data(from_date, to_date):
    """Fetch monthly sales totals per customer"""
    data = frappe.db.sql("""
        SELECT 
            si.customer,
            DATE_FORMAT(si.posting_date, '%%b %%Y') AS month,
            SUM(si.grand_total) AS sales
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %s AND %s
        GROUP BY si.customer, DATE_FORMAT(si.posting_date, '%%Y-%%m')
    """, (from_date, to_date), as_dict=True)
    return data


def get_receipts_data(from_date, to_date):
    """Fetch monthly receipts totals per customer from Payment Entry"""
    data = frappe.db.sql("""
        SELECT 
            pe.party AS customer,
            DATE_FORMAT(pe.posting_date, '%%b %%Y') AS month,
            SUM(pe.paid_amount) AS receipts
        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
          AND pe.party_type = 'Customer'
          AND pe.payment_type = 'Receive'
          AND pe.posting_date BETWEEN %s AND %s
        GROUP BY pe.party, DATE_FORMAT(pe.posting_date, '%%Y-%%m')
    """, (from_date, to_date), as_dict=True)
    return data


def get_opening_balances(from_date):
    """Fetch opening balances (outstanding before from_date)"""
    data = frappe.db.sql("""
        SELECT 
            si.customer,
            SUM(si.outstanding_amount) AS opening
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.posting_date < %s
          AND si.status IN ('Unpaid', 'Overdue')
        GROUP BY si.customer
    """, (from_date,), as_dict=True)
    return {d["customer"]: d["opening"] for d in data}


def get_columns(months):
    """Generate columns dynamically"""
    columns = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": "Opening Balance", "fieldname": "opening", "fieldtype": "Currency", "width": 150},
    ]

    for month in months:
        columns.append({
            "label": f"{month} Sales",
            "fieldname": f"{month}_sales",
            "fieldtype": "Currency",
            "width": 150
        })
        columns.append({
            "label": f"{month} Receipts",
            "fieldname": f"{month}_receipts",
            "fieldtype": "Currency",
            "width": 150
        })

    columns.append({
        "label": "Customer Ledger",
        "fieldname": "customer_ledger",
        "fieldtype": "Currency",
        "width": 150
    })

    return columns
