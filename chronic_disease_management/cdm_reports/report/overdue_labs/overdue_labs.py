"""Overdue Labs — screenings/labs past their due date."""

import frappe
from frappe import _
from frappe.utils import date_diff, nowdate


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "screening_type", "label": _("Screening Type"), "fieldtype": "Data", "width": 180},
        {"fieldname": "due_date", "label": _("Due Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "overdue_days", "label": _("Overdue Days"), "fieldtype": "Int", "width": 100},
    ]

    if not frappe.db.exists("DocType", "Complication Screening Tracker"):
        return columns, []

    items = frappe.get_all(
        "Complication Screening Tracker",
        filters={"status": ["in", ["Due", "Overdue"]], "due_date": ["<", nowdate()]},
        fields=["patient", "patient_name", "screening_type", "due_date"],
        order_by="due_date asc",
    )

    data = []
    for item in items:
        item["overdue_days"] = date_diff(nowdate(), item["due_date"])
        data.append(item)

    return columns, data
