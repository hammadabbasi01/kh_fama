# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

# import frappe


# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    from_date = filters.get("from_date") or "2000-01-01"
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    columns = get_columns()
    conditions = get_conditions(from_date, to_date)
    raw_data = get_data(conditions, from_date, to_date)

    data = []
    current_customer = None

    # Totals per customer
    total_qty = total_amount = total_sales_tax = total_total = 0

    # Grand totals
    grand_qty = grand_amount = grand_sales_tax = grand_total = 0

    for row in raw_data:
        if row.customer != current_customer:
            # Add subtotal for previous customer
            if current_customer:
                data.append({
                    "date": "",
                    "invoice_no": "",
                    "link_doctype": "",
                    "bill_no": "",
                    "garment": "Party Total",
                    "qty": total_qty,
                    "rate": "",
                    "amount": total_amount,
                    "sales_tax": total_sales_tax,
                    "total": total_total
                })
                # Add to grand totals
                grand_qty += total_qty
                grand_amount += total_amount
                grand_sales_tax += total_sales_tax
                grand_total += total_total

                # Reset customer totals
                total_qty = total_amount = total_sales_tax = total_total = 0

            # Add customer header row
            data.append({
                "date": "",
                "invoice_no": row.customer,
                "link_doctype": "Customer",
                "bill_no": "",
                "garment": "",
                "qty": "",
                "rate": "",
                "amount": "",
                "sales_tax": "",
                "total": ""
            })
            current_customer = row.customer

        # Normal invoice row
        row["link_doctype"] = "Sales Invoice"
        data.append(row)

        # Add to current customer totals
        total_qty += row.qty or 0
        total_amount += row.amount or 0
        total_sales_tax += row.sales_tax or 0
        total_total += row.total or 0

    # Final customer total (last one)
    if current_customer:
        data.append({
            "date": "",
            "invoice_no": "",
            "link_doctype": "",
            "bill_no": "",
            "garment": "Party Total",
            "qty": total_qty,
            "rate": "",
            "amount": total_amount,
            "sales_tax": total_sales_tax,
            "total": total_total
        })
        grand_qty += total_qty
        grand_amount += total_amount
        grand_sales_tax += total_sales_tax
        grand_total += total_total

    # Grand total row
    data.append({
        "date": "",
        "invoice_no": "",
        "link_doctype": "",
        "bill_no": "",
        "garment": "Grand Total",
        "qty": grand_qty,
        "rate": "",
        "amount": grand_amount,
        "sales_tax": grand_sales_tax,
        "total": grand_total
    })

    return columns, data


def get_columns():
    """Define columns for the report"""
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {
            "label": "Invoice # / Customer",
            "fieldname": "invoice_no",
            "fieldtype": "Dynamic Link",
            "options": "link_doctype",
            "width": 180
        },
        {"label": "Bill #", "fieldname": "bill_no", "fieldtype": "Data", "width": 100},
        {"label": "Garment", "fieldname": "garment", "fieldtype": "Data", "width": 150},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Sales Tax", "fieldname": "sales_tax", "fieldtype": "Currency", "width": 100},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 100},
    ]


def get_conditions(from_date, to_date):
    """Build SQL conditions if needed"""
    return f"""
        si.posting_date BETWEEN '{from_date}' AND '{to_date}'
    """


def get_data(conditions, from_date, to_date):
    """Query the Sales Invoice and Item data"""
    return frappe.db.sql(f"""
        SELECT 
            si.customer AS customer,
            si.posting_date AS date,
            si.name AS invoice_no,
            si.po_no AS bill_no,
            sii.item_name AS garment,
            sii.qty AS qty,
            sii.rate AS rate,
            sii.amount AS amount,
            (sii.amount * 0.18) AS sales_tax,
            ((sii.amount * 0.18) + sii.amount) AS total
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE {conditions} AND si.docstatus = 1 AND si.is_return = 0
        ORDER BY si.customer, si.posting_date ASC
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)
