# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    from_date = filters.get("from_date") or "2000-01-01"
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    # --- Get conditions and run query ---
    conditions = get_conditions(from_date, to_date)
    results = get_data(from_date, to_date, conditions)

    # --- Build unique month list ---
    months = sorted(list({row['month'] for row in results}))

    # --- Build unique customer list (alphabetical order) ---
    customers = sorted(list({row['customer'] for row in results}), key=lambda x: x.lower() if x else "")

    # --- Build final data ---
    final_data = []
    for customer in customers:
        customer_row = {
            'customer': customer,
            'opening': 0,
            'customer_ledger': 0
        }

        # Initialize month columns
        for month in months:
            customer_row[f"{month}_receipts"] = 0
            customer_row[f"{month}_sales"] = 0

        # Fill from query results
        for row in results:
            if row['customer'] == customer:
                customer_row['opening'] = row.get('opening') or 0
                customer_row['customer_ledger'] = row.get('customer_ledger') or 0
                customer_row[f"{row['month']}_receipts"] = row.get('receipts') or 0
                customer_row[f"{row['month']}_sales"] = row.get('sales') or 0

        final_data.append(customer_row)

    # --- Add total row ---
    total_row = {'customer': 'Total', 'opening': 0, 'customer_ledger': 0}

    # Initialize all month columns in total_row
    for month in months:
        total_row[f"{month}_receipts"] = 0
        total_row[f"{month}_sales"] = 0

    # Sum up all numeric columns
    for row in final_data:
        total_row['opening'] += row.get('opening', 0)
        total_row['customer_ledger'] += row.get('customer_ledger', 0)
        for month in months:
            total_row[f"{month}_receipts"] += row.get(f"{month}_receipts", 0)
            total_row[f"{month}_sales"] += row.get(f"{month}_sales", 0)

    # Append total row at the end
    final_data.append(total_row)

    # --- Build columns dynamically ---
    columns = get_columns(months)

    return columns, final_data


def get_conditions(from_date, to_date):
    """Return SQL condition string if needed (currently static, but flexible)."""
    return f"""
        si.docstatus = 1
        AND si.posting_date >= '{from_date}'
        AND si.posting_date <= '{to_date}'
    """


def get_data(from_date, to_date, conditions):
    """Main SQL logic to fetch data."""
    return frappe.db.sql(f'''
        SELECT 
            si.customer,
            DATE_FORMAT(si.posting_date, "%%b %%Y") AS month,
            -- Opening Balance
            (SELECT SUM(si2.outstanding_amount)
             FROM `tabSales Invoice` si2
             WHERE si2.customer = si.customer
               AND si2.docstatus = 1
               AND si2.posting_date < %(from_date)s
               AND si2.status IN ("Unpaid", "Overdue")
            ) AS opening,
            -- Receipts
            SUM(CASE WHEN si.status = "Paid" THEN si.grand_total ELSE 0 END) AS receipts,
            -- Sales
            SUM(CASE WHEN si.status IN ("Unpaid", "Overdue") THEN si.grand_total ELSE 0 END) AS sales,
            -- Closing Balance
            ((SELECT SUM(si2.outstanding_amount)
              FROM `tabSales Invoice` si2
              WHERE si2.customer = si.customer
                AND si2.docstatus = 1
                AND si2.posting_date < %(from_date)s
                AND si2.status IN ("Unpaid", "Overdue")
             ) + 
             SUM(CASE WHEN si.status IN ("Unpaid", "Overdue") THEN si.grand_total ELSE 0 END) -
             SUM(CASE WHEN si.status = "Paid" THEN si.grand_total ELSE 0 END)
            ) AS customer_ledger
        FROM `tabSales Invoice` si
        WHERE {conditions}
        GROUP BY si.customer, DATE_FORMAT(si.posting_date, "%%Y-%%m")
        ORDER BY si.customer, DATE_FORMAT(si.posting_date, "%%Y-%%m")
    ''', {"from_date": from_date, "to_date": to_date}, as_dict=True)


def get_columns(months):
    """Generate dynamic column list based on months."""
    columns = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": "Opening Balance", "fieldname": "opening", "fieldtype": "Currency", "width": 150},
    ]

    for month in months:
        columns.append({
            "label": f"{month} Receipts",
            "fieldname": f"{month}_receipts",
            "fieldtype": "Currency",
            "width": 150
        })
        columns.append({
            "label": f"{month} Sales",
            "fieldname": f"{month}_sales",
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
