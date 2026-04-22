"""Uncontrolled Patients — patients with metrics outside target ranges."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "reason", "label": _("Reason"), "fieldtype": "Data", "width": 200},
        {"fieldname": "latest_value", "label": _("Latest Value"), "fieldtype": "Float", "width": 100},
        {"fieldname": "practitioner_name", "label": _("Practitioner"), "fieldtype": "Data", "width": 150},
    ]

    if not frappe.db.exists("DocType", "Disease Enrollment"):
        return columns, []

    data = []
    settings_dt = "Disease Management Settings"
    hba1c_threshold = frappe.db.get_single_value(settings_dt, "hba1c_alert_threshold") or 9.0
    fbs_threshold = frappe.db.get_single_value(settings_dt, "fbs_high_alert_threshold") or 200

    enrollments = frappe.get_all(
        "Disease Enrollment",
        filters={"program_status": "Active"},
        fields=["patient", "patient_name", "practitioner_name"],
    )

    for e in enrollments:
        if frappe.db.exists("DocType", "Home Monitoring Entry"):
            fg = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": e.patient, "entry_type": "Fasting Glucose", "status": "Active"},
                "numeric_value", order_by="recorded_at desc",
            )
            if fg and fg >= fbs_threshold:
                data.append({**e, "reason": "High Fasting Glucose", "latest_value": fg})

    return columns, data
