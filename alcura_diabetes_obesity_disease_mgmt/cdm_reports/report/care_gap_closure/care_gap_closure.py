"""Care Gap Closure — gap type counts and average closure time."""

import frappe
from frappe import _
from frappe.utils import date_diff


def execute(filters=None):
    columns = [
        {"fieldname": "gap_type", "label": _("Gap Type"), "fieldtype": "Data", "width": 200},
        {"fieldname": "open_count", "label": _("Open"), "fieldtype": "Int", "width": 80},
        {"fieldname": "closed_count", "label": _("Closed"), "fieldtype": "Int", "width": 80},
        {"fieldname": "deferred_count", "label": _("Deferred"), "fieldtype": "Int", "width": 80},
        {"fieldname": "avg_closure_days", "label": _("Avg Closure Days"), "fieldtype": "Float", "width": 120},
    ]

    if not frappe.db.exists("DocType", "Care Gap"):
        return columns, []

    gaps = frappe.get_all(
        "Care Gap",
        fields=["gap_type", "status", "identified_on", "closed_on"],
    )

    from collections import defaultdict
    by_type = defaultdict(lambda: {"open": 0, "closed": 0, "deferred": 0, "closure_days": []})

    for g in gaps:
        t = by_type[g.gap_type]
        if g.status == "Open":
            t["open"] += 1
        elif g.status == "Closed":
            t["closed"] += 1
            if g.identified_on and g.closed_on:
                t["closure_days"].append(date_diff(g.closed_on, g.identified_on))
        elif g.status == "Deferred":
            t["deferred"] += 1

    data = []
    for gap_type, counts in sorted(by_type.items()):
        avg = round(sum(counts["closure_days"]) / len(counts["closure_days"]), 1) if counts["closure_days"] else None
        data.append({
            "gap_type": gap_type,
            "open_count": counts["open"],
            "closed_count": counts["closed"],
            "deferred_count": counts["deferred"],
            "avg_closure_days": avg,
        })

    return columns, data
