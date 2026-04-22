"""Patient Portal Engagement Report — self-entry activity metrics."""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "portal_active", "label": _("Portal Active"), "fieldtype": "Data", "width": 100},
        {"fieldname": "entries_logged", "label": _("Entries (30d)"), "fieldtype": "Int", "width": 100},
        {"fieldname": "compliance", "label": _("Compliance"), "fieldtype": "Data", "width": 100},
    ]

    if not frappe.db.exists("DocType", "Disease Enrollment"):
        return columns, []

    enrollments = frappe.get_all(
        "Disease Enrollment",
        filters={"program_status": "Active"},
        fields=["patient", "patient_name"],
    )

    from_date = add_days(nowdate(), -30)
    data = []
    for e in enrollments:
        row = {"patient": e.patient, "patient_name": e.patient_name}
        row["portal_active"] = "No"
        row["entries_logged"] = 0
        row["compliance"] = "\u2014"

        patient_user = frappe.db.get_value("Patient", e.patient, "user_id")
        if patient_user:
            row["portal_active"] = "Yes"

        if frappe.db.exists("DocType", "Home Monitoring Entry"):
            count = frappe.db.count(
                "Home Monitoring Entry",
                {
                    "patient": e.patient,
                    "is_patient_entered": 1,
                    "status": "Active",
                    "recorded_at": [">=", from_date],
                },
            )
            row["entries_logged"] = count
            if count >= 20:
                row["compliance"] = "Good"
            elif count >= 10:
                row["compliance"] = "Moderate"
            elif count > 0:
                row["compliance"] = "Low"

        data.append(row)

    return columns, data
