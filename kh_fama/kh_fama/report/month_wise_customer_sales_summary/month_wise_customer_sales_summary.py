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

    # Add "As On <Previous Month>" column
    prev_month = add_months(from_date, -1)
    prev_label = f"As On {formatdate(prev_month, 'MMM-yy')}"
    columns.append({
        "label": prev_label,
        "fieldname": f"as_on_{formatdate(prev_month, 'MMM-yy').lower().replace('-', '_')}",
        "fieldtype": "Currency",
        "width": 120
    })

    # Add dynamic month columns
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

    if customer_filter:
        customers = frappe.db.get_all("Customer", fields=["name"], filters={"name": customer_filter})
    else:
        customers = frappe.db.get_all("Customer", fields=["name"], order_by="name")

    grand_totals = {k: {} for k in ["Billing", "Tax Ded.", "Other Ded.", "Received", "Total", "Balance"]}
    sr_no = 1

    prev_month = add_months(from_date, -1)
    prev_end_date = prev_month + relativedelta(day=31)
    prev_label = f"As On {formatdate(prev_month, 'MMM-yy')}"
    prev_field = f"as_on_{formatdate(prev_month, 'MMM-yy').lower().replace('-', '_')}"

    for cust in customers:
        customer_name = cust.name
        customer_rows = []
        rows = {k: {} for k in ["Billing", "Tax Ded.", "Other Ded.", "Received", "Total", "Balance"]}
        total_summary = {k: 0 for k in rows.keys()}

        # --- Calculate cumulative data up to previous month ---
        billing_prev = frappe.db.sql("""
            SELECT COALESCE(SUM(base_total), 0)
            FROM `tabSales Invoice`
            WHERE customer = %s AND posting_date <= %s AND docstatus = 1
        """, (customer_name, prev_end_date))[0][0]

        tax_ded_prev = frappe.db.sql("""
            SELECT COALESCE(SUM(total_taxes_and_charges), 0)
            FROM `tabSales Invoice`
            WHERE customer = %s AND posting_date <= %s AND docstatus = 1
        """, (customer_name, prev_end_date))[0][0]

        other_ded_prev = 0

        received_prev = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM `tabPayment Entry`
            WHERE party_type = 'Customer'
              AND party = %s
              AND payment_type = 'Receive'
              AND posting_date <= %s
              AND docstatus = 1
        """, (customer_name, prev_end_date))[0][0]

        total_prev = billing_prev + tax_ded_prev + other_ded_prev
        balance_prev = total_prev - received_prev

        # Save cumulative values
        rows["Billing"][prev_label] = billing_prev
        rows["Tax Ded."][prev_label] = tax_ded_prev
        rows["Other Ded."][prev_label] = other_ded_prev
        rows["Received"][prev_label] = received_prev
        rows["Total"][prev_label] = total_prev
        rows["Balance"][prev_label] = balance_prev

        # --- Add monthly data ---
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

            # Update totals
            for key in total_summary.keys():
                total_summary[key] += rows[key].get(month_key, 0)

            # Add to grand totals
            for key in rows.keys():
                grand_totals[key][month_key] = grand_totals[key].get(month_key, 0) + rows[key][month_key]

            current = add_months(current, 1)

        # Skip customers with no transactions
        if sum(total_summary.values()) == 0 and total_prev == 0:
            continue

        # Prepare rows per customer
        for idx, label in enumerate(rows.keys()):
            row_data = {
                "sr_no": sr_no if label == "Billing" else "",
                "customer_name": f"<b style='font-size:13px'>{customer_name}</b>" if label == "Billing" else "",
                "detail_type": label,
                prev_field: rows[label].get(prev_label, 0)
            }

            for month, value in rows[label].items():
                if month != prev_label:
                    row_data[month.lower().replace('-', '_')] = value

            row_data["total"] = total_summary[label] + rows[label].get(prev_label, 0)
            customer_rows.append(row_data)

        data.extend(customer_rows)
        sr_no += 1

    # --- GRAND TOTAL SECTION ---
    for label in grand_totals.keys():
        row = {"sr_no": "", "customer_name": "<b>G. Total</b>", "detail_type": label, prev_field: 0}
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
