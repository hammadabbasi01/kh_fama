import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Process", "fieldname": "process", "fieldtype": "Data", "width": 120},
        {"label": "Customer", "fieldname": "cust_no", "fieldtype": "Data", "width": 150},
        {"label": "Doc No", "fieldname": "doc_no", "fieldtype": "Data", "width": 200},
        {"label": "Entry Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Style No", "fieldname": "style", "fieldtype": "Data", "width": 100},
        {"label": "Style Description", "fieldname": "description", "fieldtype": "Data", "width": 200},
        {"label": "Qty", "fieldname": "sum_qty", "fieldtype": "Float", "width": 100},
        {"label": "Customer Total Qty", "fieldname": "customer_total_qty", "fieldtype": "Float", "width": 150},
    ]


def get_data(filters):
    # conditions = "se.docstatus = 1"
    conditions = ""

    if filters.get("from_date"):
        conditions += f" se.posting_date >= '{filters['from_date']}'"
    if filters.get("to_date"):
        conditions += f" AND se.posting_date <= '{filters['to_date']}'"

    finished_material_condition = """
        (sed.s_warehouse IS NULL OR sed.s_warehouse = '')
        AND sed.t_warehouse LIKE '%Finished%'
    """

    query = f"""
        SELECT
            se.process AS process,
            se.cust_no AS cust_no,
            se.name AS doc_no,
            se.posting_date AS posting_date,
            sed.style AS style,
            sed.description AS description,
            sed.qty AS sum_qty
        FROM
            `tabStock Entry` se
        INNER JOIN
            `tabStock Entry Detail` sed ON sed.parent = se.name
        WHERE
            {conditions} AND {finished_material_condition}
        ORDER BY
            se.process, se.cust_no, se.posting_date ASC
    """
    raw_data = frappe.db.sql(query, as_dict=True)

    # Group data by process and customer
    grouped_data = []
    process_totals = {}
    customer_totals = {}

    for row in raw_data:
        process_key = row["process"]
        customer_key = (row["process"], row["cust_no"])

        # Initialize totals
        if process_key not in process_totals:
            process_totals[process_key] = 0
        if customer_key not in customer_totals:
            customer_totals[customer_key] = 0

        # Update totals
        process_totals[process_key] += row["sum_qty"]
        customer_totals[customer_key] += row["sum_qty"]

        # Append individual rows
        grouped_data.append({
            "process": row["process"],
            "cust_no": row["cust_no"],
            "doc_no": row["doc_no"],
            "posting_date": row["posting_date"],
            "style": row["style"],
            "description": row["description"],
            "sum_qty": row["sum_qty"],
            "customer_total_qty": ""
        })

    # Add customer-wise totals
    for (process, cust_no), total_qty in customer_totals.items():
        grouped_data.append({
            "process": process,
            "cust_no": cust_no,
            "doc_no": "",
            "posting_date": "",
            "style": "",
            "description": f"{cust_no} Total",
            "sum_qty": "",
            "customer_total_qty": total_qty
        })

    # Add process-wise totals
    for process, total_qty in process_totals.items():
        grouped_data.append({
            "process": process,
            "cust_no": "",
            "doc_no": "",
            "posting_date": "",
            "style": "",
            "description": f"{process} Total",
            "sum_qty": "",
            "customer_total_qty": total_qty
        })

    return grouped_data