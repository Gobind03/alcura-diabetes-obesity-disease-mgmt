"""Obesity Registry — all patients enrolled in obesity programs."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "obesity_class", "label": _("Obesity Class"), "fieldtype": "Data", "width": 120},
        {"fieldname": "baseline_weight", "label": _("Baseline Wt"), "fieldtype": "Float", "width": 100},
        {"fieldname": "current_weight", "label": _("Current Wt"), "fieldtype": "Float", "width": 100},
        {"fieldname": "pct_change", "label": _("% Change"), "fieldtype": "Float", "width": 90},
        {"fieldname": "open_alerts", "label": _("Open Alerts"), "fieldtype": "Int", "width": 90},
    ]

    if not frappe.db.exists("DocType", "Disease Enrollment"):
        return columns, []

    enrollments = frappe.get_all(
        "Disease Enrollment",
        filters={"disease_type": ["in", ["Obesity", "Combined Metabolic"]]},
        fields=["name", "patient", "patient_name"],
        order_by="enrollment_date desc",
    )

    data = []
    for e in enrollments:
        row = {"patient": e.patient, "patient_name": e.patient_name}
        row["obesity_class"] = None
        row["baseline_weight"] = None
        row["current_weight"] = None
        row["pct_change"] = None
        row["open_alerts"] = 0

        if frappe.db.exists("DocType", "Obesity Profile"):
            profile = frappe.db.get_value(
                "Obesity Profile",
                {"enrollment": e.name, "status": "Active"},
                ["obesity_class", "baseline_weight"],
                as_dict=True,
            )
            if profile:
                row["obesity_class"] = profile.obesity_class
                row["baseline_weight"] = profile.baseline_weight

        if frappe.db.exists("DocType", "Home Monitoring Entry"):
            w = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": e.patient, "entry_type": "Weight", "status": "Active"},
                "numeric_value",
                order_by="recorded_at desc",
            )
            if w:
                row["current_weight"] = w
                if row["baseline_weight"] and row["baseline_weight"] > 0:
                    row["pct_change"] = round(((w - row["baseline_weight"]) / row["baseline_weight"]) * 100, 1)

        if frappe.db.exists("DocType", "CDM Alert"):
            row["open_alerts"] = frappe.db.count(
                "CDM Alert", {"patient": e.patient, "status": ["in", ["Open", "Acknowledged"]]}
            )

        data.append(row)

    return columns, data
