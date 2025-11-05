# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

# import frappe


# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, formatdate, add_months
from dateutil.relativedelta import relativedelta


def execute(filters=None):
    if not filters:
        filters = {}

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    customer_filter = filters.get("customer")

    columns = get_columns(from_date, to_date)
    data = get_data(from_date, to_date, customer_filter)

    return columns, data


def get_columns(from_date, to_date):
    """Generate dynamic month columns between date range"""
    columns = [
        {"label": "S. No", "fieldname": "sr_no", "fieldtype": "Data", "width": 60},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": "Detail Type", "fieldname": "detail_type", "fieldtype": "Data", "width": 150},
    ]

    current = from_date.replace(day=1)
    while current <= to_date:
        month_label = formatdate(current, "MMM-yy")
        columns.append({
            "label": month_label,
            "fieldname": month_label.lower().replace('-', '_'),
            "fieldtype": "Currency",
            "width": 120
        })
        current = add_months(current, 1)

    columns.append({
        "label": "Total",
        "fieldname": "total",
        "fieldtype": "Currency",
        "width": 120
    })
    return columns


def get_data(from_date, to_date, customer_filter=None):
    """Fetch and prepare data for each customer and month"""
    data = []

    # ✅ Apply customer filter if selected
    if customer_filter:
        customers = frappe.db.get_all("Customer", fields=["name"], filters={"name": customer_filter})
    else:
        customers = frappe.db.get_all("Customer", fields=["name"], order_by="name")

    # To collect grand totals
    grand_totals = {
        "Billing": {},
        "Tax Ded.": {},
        "Other Ded.": {},
        "Received": {},
        "Total": {},
        "Balance": {}
    }

    sr_no = 1
    for cust in customers:
        customer_name = cust.name
        customer_rows = []

        rows = {
            "Billing": {},
            "Tax Ded.": {},
            "Other Ded.": {},
            "Received": {},
            "Total": {},
            "Balance": {}
        }
        total_summary = {key: 0 for key in rows.keys()}

        current = from_date.replace(day=1)
        while current <= to_date:
            month_key = formatdate(current, "MMM-yy")
            month_start = current
            month_end = (month_start + relativedelta(day=31))

            billing = frappe.db.sql("""
                SELECT COALESCE(SUM(base_total), 0)
                FROM `tabSales Invoice`
                WHERE customer = %s
                  AND posting_date BETWEEN %s AND %s
                  AND docstatus = 1
            """, (customer_name, month_start, month_end))[0][0]

            tax_ded = frappe.db.sql("""
                SELECT COALESCE(SUM(total_taxes_and_charges), 0)
                FROM `tabSales Invoice`
                WHERE customer = %s
                  AND posting_date BETWEEN %s AND %s
                  AND docstatus = 1
            """, (customer_name, month_start, month_end))[0][0]

            other_ded = 0

            received = frappe.db.sql("""
                SELECT COALESCE(SUM(paid_amount), 0)
                FROM `tabPayment Entry`
                WHERE party_type = 'Customer'
                  AND party = %s
                  AND payment_type = 'Receive'
                  AND posting_date BETWEEN %s AND %s
                  AND docstatus = 1
            """, (customer_name, month_start, month_end))[0][0]

            total = billing + tax_ded + other_ded
            balance = total - received

            # Save monthly data
            rows["Billing"][month_key] = billing
            rows["Tax Ded."][month_key] = tax_ded
            rows["Other Ded."][month_key] = other_ded
            rows["Received"][month_key] = received
            rows["Total"][month_key] = total
            rows["Balance"][month_key] = balance

            # Update per-customer total
            total_summary["Billing"] += billing
            total_summary["Tax Ded."] += tax_ded
            total_summary["Other Ded."] += other_ded
            total_summary["Received"] += received
            total_summary["Total"] += total
            total_summary["Balance"] += balance

            # --- Add to grand total ---
            for k, v in rows.items():
                grand_totals[k][month_key] = grand_totals[k].get(month_key, 0) + v[month_key]

            current = add_months(current, 1)

        # ✅ Skip customer if there’s no transaction in this period
        total_activity = (
            total_summary["Billing"]
            + total_summary["Tax Ded."]
            + total_summary["Received"]
        )
        if total_activity == 0:
            continue  # skip this customer completely

        # Prepare output rows for this customer
        for idx, label in enumerate(rows.keys()):
            row_data = {
                "sr_no": sr_no if label == "Billing" else "",
                "customer_name": f"<b style='font-size:13px'>{customer_name}</b>" if label == "Billing" else "",
                "detail_type": label
            }

            for month, value in rows[label].items():
                row_data[month.lower().replace('-', '_')] = value
            row_data["total"] = total_summary[label]
            customer_rows.append(row_data)

        data.extend(customer_rows)
        sr_no += 1

    # --- GRAND TOTAL SECTION ---
    for label in grand_totals.keys():
        row = {"sr_no": "", "customer_name": "<b>G. Total</b>", "detail_type": label}
        total_value = 0

        current = from_date.replace(day=1)
        while current <= to_date:
            month_key = formatdate(current, "MMM-yy")
            field = month_key.lower().replace('-', '_')
            value = grand_totals[label].get(month_key, 0)
            row[field] = value
            total_value += value
            current = add_months(current, 1)

        row["total"] = total_value
        data.append(row)

    return data
