"""Diabetes Registry — all patients enrolled in diabetes programs."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "practitioner_name", "label": _("Practitioner"), "fieldtype": "Data", "width": 150},
        {"fieldname": "program_status", "label": _("Status"), "fieldtype": "Data", "width": 100},
        {"fieldname": "enrollment_date", "label": _("Enrolled"), "fieldtype": "Date", "width": 100},
        {"fieldname": "latest_fasting_glucose", "label": _("Latest FBS"), "fieldtype": "Float", "width": 100},
        {"fieldname": "open_alerts", "label": _("Open Alerts"), "fieldtype": "Int", "width": 90},
        {"fieldname": "open_gaps", "label": _("Open Gaps"), "fieldtype": "Int", "width": 90},
    ]

    if not frappe.db.exists("DocType", "Disease Enrollment"):
        return columns, []

    enrollments = frappe.get_all(
        "Disease Enrollment",
        filters={"disease_type": ["in", ["Diabetes", "Combined Metabolic", "Prediabetes / Metabolic Risk"]]},
        fields=["name", "patient", "patient_name", "practitioner_name", "program_status", "enrollment_date"],
        order_by="enrollment_date desc",
    )

    data = []
    for e in enrollments:
        row = {**e}
        row["latest_fasting_glucose"] = None
        row["open_alerts"] = 0
        row["open_gaps"] = 0

        if frappe.db.exists("DocType", "Home Monitoring Entry"):
            fg = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": e.patient, "entry_type": "Fasting Glucose", "status": "Active"},
                "numeric_value",
                order_by="recorded_at desc",
            )
            if fg:
                row["latest_fasting_glucose"] = fg

        if frappe.db.exists("DocType", "CDM Alert"):
            row["open_alerts"] = frappe.db.count(
                "CDM Alert",
                {"patient": e.patient, "status": ["in", ["Open", "Acknowledged"]]},
            )

        if frappe.db.exists("DocType", "Care Gap"):
            row["open_gaps"] = frappe.db.count(
                "Care Gap",
                {"patient": e.patient, "status": "Open"},
            )

        data.append(row)

    return columns, data
