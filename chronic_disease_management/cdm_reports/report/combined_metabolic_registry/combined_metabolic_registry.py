"""Combined Metabolic Registry — all CDM-enrolled patients."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "disease_type", "label": _("Program"), "fieldtype": "Data", "width": 130},
        {"fieldname": "latest_fasting_glucose", "label": _("Latest FBS"), "fieldtype": "Float", "width": 100},
        {"fieldname": "current_weight", "label": _("Weight"), "fieldtype": "Float", "width": 90},
        {"fieldname": "open_gaps", "label": _("Gaps"), "fieldtype": "Int", "width": 80},
        {"fieldname": "open_alerts", "label": _("Alerts"), "fieldtype": "Int", "width": 80},
    ]

    if not frappe.db.exists("DocType", "Disease Enrollment"):
        return columns, []

    enrollments = frappe.get_all(
        "Disease Enrollment",
        filters={"program_status": "Active"},
        fields=["name", "patient", "patient_name", "disease_type"],
        order_by="enrollment_date desc",
    )

    data = []
    for e in enrollments:
        row = {**e, "latest_fasting_glucose": None, "current_weight": None, "open_gaps": 0, "open_alerts": 0}

        if frappe.db.exists("DocType", "Home Monitoring Entry"):
            fg = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": e.patient, "entry_type": "Fasting Glucose", "status": "Active"},
                "numeric_value", order_by="recorded_at desc",
            )
            if fg:
                row["latest_fasting_glucose"] = fg

            w = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": e.patient, "entry_type": "Weight", "status": "Active"},
                "numeric_value", order_by="recorded_at desc",
            )
            if w:
                row["current_weight"] = w

        if frappe.db.exists("DocType", "Care Gap"):
            row["open_gaps"] = frappe.db.count("Care Gap", {"patient": e.patient, "status": "Open"})
        if frappe.db.exists("DocType", "CDM Alert"):
            row["open_alerts"] = frappe.db.count("CDM Alert", {"patient": e.patient, "status": ["in", ["Open", "Acknowledged"]]})

        data.append(row)

    return columns, data
