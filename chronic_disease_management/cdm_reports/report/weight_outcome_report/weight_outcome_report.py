"""Weight Outcome Report — baseline vs current weight for all enrolled patients."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "baseline_weight", "label": _("Baseline Wt"), "fieldtype": "Float", "width": 100},
        {"fieldname": "current_weight", "label": _("Current Wt"), "fieldtype": "Float", "width": 100},
        {"fieldname": "delta", "label": _("Delta (kg)"), "fieldtype": "Float", "width": 90},
        {"fieldname": "pct_change", "label": _("% Change"), "fieldtype": "Float", "width": 90},
    ]

    if not frappe.db.exists("DocType", "Obesity Profile"):
        return columns, []

    profiles = frappe.get_all(
        "Obesity Profile",
        filters={"status": "Active"},
        fields=["patient", "patient_name", "baseline_weight", "enrollment"],
    )

    data = []
    for p in profiles:
        row = {"patient": p.patient, "patient_name": p.patient_name, "baseline_weight": p.baseline_weight}
        row["current_weight"] = None
        row["delta"] = None
        row["pct_change"] = None

        if frappe.db.exists("DocType", "Home Monitoring Entry") and p.baseline_weight:
            w = frappe.db.get_value(
                "Home Monitoring Entry",
                {"patient": p.patient, "entry_type": "Weight", "status": "Active"},
                "numeric_value", order_by="recorded_at desc",
            )
            if w:
                row["current_weight"] = w
                row["delta"] = round(w - p.baseline_weight, 2)
                if p.baseline_weight > 0:
                    row["pct_change"] = round((row["delta"] / p.baseline_weight) * 100, 1)

        data.append(row)

    return columns, data
