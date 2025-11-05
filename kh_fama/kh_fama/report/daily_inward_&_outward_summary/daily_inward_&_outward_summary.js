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
    ],
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Apply styles based on row type
        if (data) {
            if (data.description && data.description.includes("Total")) {
                // Style for customer or process totals
                return `<span style="background-color:#e6f7ff;font-weight:bold;">${value}</span>`;
            } else if (data.description && data.description.includes("Grand Total")) {
                // Style for grand total
                return `<span style="background-color:#ffe6e6;font-weight:bold;">${value}</span>`;
            }
            else {
                //row gray color
                return  `<span style="background-color:#f9f9f9;">${value}</span>`;
            }
        }

        return value;
    }

};


