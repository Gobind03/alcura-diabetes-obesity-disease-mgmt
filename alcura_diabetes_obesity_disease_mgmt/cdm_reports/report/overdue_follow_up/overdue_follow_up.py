"""Overdue Follow-Up — patients with overdue scheduled reviews."""

import frappe
from frappe import _
from frappe.utils import date_diff, nowdate


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "practitioner_name", "label": _("Practitioner"), "fieldtype": "Data", "width": 150},
        {"fieldname": "review_type", "label": _("Review Type"), "fieldtype": "Data", "width": 150},
        {"fieldname": "due_date", "label": _("Due Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "overdue_days", "label": _("Overdue Days"), "fieldtype": "Int", "width": 100},
    ]

    if not frappe.db.exists("DocType", "Disease Review Sheet"):
        return columns, []

    reviews = frappe.get_all(
        "Disease Review Sheet",
        filters={"status": "Scheduled", "due_date": ["<", nowdate()]},
        fields=["patient", "patient_name", "practitioner_name", "review_type", "due_date"],
        order_by="due_date asc",
    )

    data = []
    for r in reviews:
        r["overdue_days"] = date_diff(nowdate(), r["due_date"])
        data.append(r)

    return columns, data
