"""HbA1c Improvement Report — baseline vs current HbA1c."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "baseline_hba1c", "label": _("Baseline HbA1c"), "fieldtype": "Float", "width": 110},
        {"fieldname": "current_hba1c", "label": _("Current HbA1c"), "fieldtype": "Float", "width": 110},
        {"fieldname": "delta", "label": _("Delta"), "fieldtype": "Float", "width": 80},
    ]

    if not frappe.db.exists("DocType", "Disease Baseline Assessment"):
        return columns, []

    baselines = frappe.get_all(
        "Disease Baseline Assessment",
        filters={"hba1c": ["is", "set"]},
        fields=["patient", "patient_name", "hba1c"],
    )

    data = []
    for b in baselines:
        row = {"patient": b.patient, "patient_name": b.patient_name, "baseline_hba1c": b.hba1c}
        row["current_hba1c"] = None
        row["delta"] = None

        if frappe.db.exists("DocType", "Lab Test"):
            lab = frappe.db.get_value(
                "Lab Test",
                {"patient": b.patient, "template": ["like", "%HbA1c%"], "docstatus": 1},
                "result_value",
                order_by="result_date desc",
            )
            if lab:
                try:
                    current = float(lab)
                    row["current_hba1c"] = current
                    row["delta"] = round(current - b.hba1c, 2)
                except (ValueError, TypeError):
                    pass

        data.append(row)

    return columns, data
