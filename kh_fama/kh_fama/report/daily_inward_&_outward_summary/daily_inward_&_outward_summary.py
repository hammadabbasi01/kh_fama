# ...existing code...
import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Process", "fieldname": "process", "fieldtype": "Data", "width": 140},
        {"label": "Customer", "fieldname": "cust_no", "fieldtype": "Data", "width": 180},
        {"label": "Doc No", "fieldname": "doc_no", "fieldtype": "Data", "width": 160},
        {"label": "Entry Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Style No", "fieldname": "style", "fieldtype": "Data", "width": 120},
        {"label": "Style Description", "fieldname": "description", "fieldtype": "Data", "width": 300},
        {"label": "In Qty", "fieldname": "in_qty", "fieldtype": "Float", "width": 100},
        {"label": "Out Qty", "fieldname": "out_qty", "fieldtype": "Float", "width": 100},
    ]


def get_data(filters):
    # --- Conditions (make safe default)
    # conditions = "se.docstatus = 1"
    conditions = ""

    if filters:
        if filters.get("from_date"):
            conditions += f" se.posting_date >= '{filters['from_date']}'"
        if filters.get("to_date"):
            conditions += f" AND se.posting_date <= '{filters['to_date']}'"
        if filters.get("process"):
            conditions += f" AND se.process = '{filters['process']}'"
        if filters.get("customer"):
            conditions += f" AND se.cust_no = '{filters['customer']}'"
        if filters.get("style"):
            conditions += f" AND sed.style = '{filters['style']}'"
        if filters.get("sales_order"):
            conditions += f" AND se.sales_order = '{filters['sales_order']}'"
        if filters.get("delivery_note"):
            conditions += f" AND se.delivery_note = '{filters['delivery_note']}'"


    finished_material_condition = """
        (sed.s_warehouse IS NULL OR sed.s_warehouse = '')
        AND sed.t_warehouse LIKE '%Finished%'
    """

    material_issue_condition = """
        (sed.s_warehouse IS NOT NULL AND sed.s_warehouse Like '%Finished%')
        AND se.stock_entry_type = 'Material Issue'
    """
    # --- Query: compute in_qty when moved to Finished (and s_warehouse empty),
    # and out_qty when Stock Entry is Material Issue
    query = f"""
        SELECT
            se.process AS process,
            se.cust_no AS cust_no,
            se.name AS doc_no,
            se.posting_date AS posting_date,
            sed.style AS style,
            sed.description AS description,
            CASE
                WHEN {finished_material_condition}
                THEN sed.qty
                ELSE 0
            END AS in_qty,
            CASE
                WHEN {material_issue_condition} THEN sed.qty
                ELSE 0
            END AS out_qty
        FROM
            `tabStock Entry` se
        INNER JOIN
            `tabStock Entry Detail` sed ON sed.parent = se.name
        WHERE
            {conditions} and   {finished_material_condition} OR {material_issue_condition }
        ORDER BY
            se.process, se.cust_no, se.posting_date, se.name
    """

    raw_data = frappe.db.sql(query, as_dict=True)
    if not raw_data:
        return []

    grouped_data = []
    current_process = None
    current_customer = None

    customer_total_in = 0
    customer_total_out = 0
    process_total_in = 0
    process_total_out = 0
    grand_total_in = 0
    grand_total_out = 0

    for row in raw_data:
        process = row.get("process")
        customer = row.get("cust_no")

        # When customer changes -> append customer totals
        if current_customer and customer != current_customer:
            grouped_data.append({
                "process": "",
                "cust_no": current_customer,
                "doc_no": "",
                "posting_date": "",
                "style": "",
                "description": f"{current_customer} Total",
                "in_qty": round(customer_total_in, 2),
                "out_qty": round(customer_total_out, 2),
            })
            customer_total_in = 0
            customer_total_out = 0

        # When process changes -> append process totals (after customer total if any)
        if current_process and process != current_process:
            grouped_data.append({
                "process": current_process,
                "cust_no": "",
                "doc_no": "",
                "posting_date": "",
                "style": "",
                "description": f"{current_process} Total",
                "in_qty": round(process_total_in, 2),
                "out_qty": round(process_total_out, 2),
            })
            process_total_in = 0
            process_total_out = 0

        # Append current row (make sure fields present)
        grouped_data.append({
            "process": row.get("process"),
            "cust_no": row.get("cust_no"),
            "doc_no": row.get("doc_no"),
            "posting_date": row.get("posting_date"),
            "style": row.get("style"),
            "description": row.get("description"),
            "in_qty": row.get("in_qty") or 0,
            "out_qty": row.get("out_qty") or 0,
        })

        # accumulate totals
        customer_total_in += row.get("in_qty") or 0
        customer_total_out += row.get("out_qty") or 0
        process_total_in += row.get("in_qty") or 0
        process_total_out += row.get("out_qty") or 0
        grand_total_in += row.get("in_qty") or 0
        grand_total_out += row.get("out_qty") or 0

        current_customer = customer
        current_process = process

    # Final customer total
    if current_customer:
        grouped_data.append({
            "process": "",
            "cust_no": current_customer,
            "doc_no": "",
            "posting_date": "",
            "style": "",
            "description": f"{current_customer} Total",
            "in_qty": round(customer_total_in, 2),
            "out_qty": round(customer_total_out, 2),
        })

    # Final process total
    if current_process:
        grouped_data.append({
            "process": current_process,
            "cust_no": "",
            "doc_no": "",
            "posting_date": "",
            "style": "",
            "description": f"{current_process} Total",
            "in_qty": round(process_total_in, 2),
            "out_qty": round(process_total_out, 2),
        })

    # Grand total
    grouped_data.append({
        "process": "",
        "cust_no": "",
        "doc_no": "",
        "posting_date": "",
        "style": "",
        "description": "Grand Total",
        "in_qty": round(grand_total_in, 2),
        "out_qty": round(grand_total_out, 2),
    })

    return grouped_data
# ...existing code...