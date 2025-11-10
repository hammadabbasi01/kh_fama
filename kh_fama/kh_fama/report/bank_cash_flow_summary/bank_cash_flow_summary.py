# Copyright (c) 2025, hammad and contributors
# For license information, please see license.txt

# import frappe


# Copyright (c) 2025, Hammad
# For license information, please see license.txt

import frappe
import random

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data()
    
    return columns, data


def get_columns():
    return [
        {"label": "Head of Account", "fieldname": "head_of_account", "fieldtype": "Data", "width": 250},
        {"label": "BAHL-CP", "fieldname": "bahl_cp", "fieldtype": "Currency", "width": 120},
        {"label": "HMBL", "fieldname": "hmbl", "fieldtype": "Currency", "width": 120},
        {"label": "MBL", "fieldname": "mbl", "fieldtype": "Currency", "width": 120},
        {"label": "MBL Gulberg", "fieldname": "mbl_gulberg", "fieldtype": "Currency", "width": 120},
        {"label": "BDI", "fieldname": "bdi", "fieldtype": "Currency", "width": 120},
        {"label": "BAHL-CA", "fieldname": "bahl_ca", "fieldtype": "Currency", "width": 120},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 130},
    ]


def get_data():
    # Define static Head of Accounts (from your screenshot)
    heads = [
        "Opening Balance",
        "Sales Recovery",
        "Transfer-In",
        "Total:",
        "Transfer-Out",
        "Total:",
        "Assets-Pumps",
        "Assets-Solar System",
        "Total:",
        "Advances to Contractors",
        "BPS Wages",
        "Total:",
        "Viscar Wages",
        "Washing Exp.",
        "Total:"
    ]

    data = []
    for head in heads:
        # Fill totals as blank rows (just format like in Excel)
        if head == "Total:":
            row = {
                "head_of_account": head,
                "bahl_cp": "",
                "hmbl": "",
                "mbl": "",
                "mbl_gulberg": "",
                "bdi": "",
                "bahl_ca": "",
                "total": ""
            }
        else:
            # Random example values for now
            bahl_cp = random.randint(1000, 5000)
            hmbl = random.randint(1000, 5000)
            mbl = random.randint(1000, 5000)
            mbl_gulberg = random.randint(1000, 5000)
            bdi = random.randint(1000, 5000)
            bahl_ca = random.randint(1000, 5000)

            total = bahl_cp + hmbl + mbl + mbl_gulberg + bdi + bahl_ca

            row = {
                "head_of_account": head,
                "bahl_cp": bahl_cp,
                "hmbl": hmbl,
                "mbl": mbl,
                "mbl_gulberg": mbl_gulberg,
                "bdi": bdi,
                "bahl_ca": bahl_ca,
                "total": total
            }

        data.append(row)

    return data
