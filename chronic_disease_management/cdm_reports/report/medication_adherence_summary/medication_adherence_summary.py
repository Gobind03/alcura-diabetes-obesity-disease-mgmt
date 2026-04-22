"""Medication Adherence Summary — per-patient adherence metrics."""

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 120},
        {"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "medication_name", "label": _("Medication"), "fieldtype": "Data", "width": 180},
        {"fieldname": "adherence_pct", "label": _("Adherence %"), "fieldtype": "Float", "width": 100},
        {"fieldname": "missed_count", "label": _("Missed"), "fieldtype": "Int", "width": 80},
        {"fieldname": "common_reason", "label": _("Common Reason"), "fieldtype": "Data", "width": 150},
    ]

    if not frappe.db.exists("DocType", "Medication Adherence Log"):
        return columns, []

    logs = frappe.get_all(
        "Medication Adherence Log",
        fields=["patient", "patient_name", "medication_name", "adherence_status", "reason_category"],
    )

    from collections import defaultdict
    grouped = defaultdict(lambda: {"taken": 0, "missed": 0, "total": 0, "reasons": defaultdict(int), "patient_name": ""})

    for l in logs:
        key = (l.patient, l.medication_name)
        g = grouped[key]
        g["total"] += 1
        g["patient_name"] = l.patient_name
        if l.adherence_status == "Taken":
            g["taken"] += 1
        elif l.adherence_status == "Missed":
            g["missed"] += 1
            if l.reason_category:
                g["reasons"][l.reason_category] += 1

    data = []
    for (patient, med), g in sorted(grouped.items()):
        pct = round((g["taken"] / g["total"]) * 100, 1) if g["total"] else None
        common = max(g["reasons"], key=g["reasons"].get) if g["reasons"] else None
        data.append({
            "patient": patient,
            "patient_name": g["patient_name"],
            "medication_name": med,
            "adherence_pct": pct,
            "missed_count": g["missed"],
            "common_reason": common,
        })

    return columns, data
