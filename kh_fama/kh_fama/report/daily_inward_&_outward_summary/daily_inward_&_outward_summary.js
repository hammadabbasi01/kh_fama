// Copyright (c) 2025, hammad and contributors
// For license information, please see license.txt
/* eslint-disable */



frappe.query_reports["Daily Inward & Outward Summary"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0
        },
        {
            "fieldname": "sales_order",
            "label": "Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "reqd": 0
        },
        {
            "fieldname": "delivery_note",
            "label": "Delivery Note",
            "fieldtype": "Link",
            "options": "Delivery Note",
            "reqd": 0
        },
        {
            "fieldname": "process",
            "label": "Process",
            "fieldtype": "Select",
            "options": [
                "",
                "Wash",
                "Garment Dyeing",
                "Denim"
            ],
            "reqd": 0
        },
        {
            "fieldname": "style",
            "label": "Style",
            "fieldtype": "Data",
            "reqd": 0
        }
    ]
};
