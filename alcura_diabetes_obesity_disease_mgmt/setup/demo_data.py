"""Seed / demo data utilities for development and testing environments.

Usage:
    bench --site dev.localhost execute \
        alcura_diabetes_obesity_disease_mgmt.setup.demo_data.create_demo_data
"""

import frappe
from frappe.utils import add_days, nowdate, now_datetime


_DEMO_PREFIX = "CDM-DEMO"


def create_demo_data():
	"""Create sample patients, enrollments, profiles, monitoring entries, etc."""
	frappe.flags.in_demo_data = True

	patients = _ensure_demo_patients()
	enrollments = _create_enrollments(patients)
	_create_profiles(enrollments)
	_create_monitoring_entries(patients, enrollments)
	_create_care_plans(enrollments)
	_create_alerts(patients, enrollments)
	_create_screenings(patients, enrollments)
	_create_care_gaps(patients, enrollments)
	_create_coordinator_actions(patients, enrollments)

	frappe.db.commit()
	frappe.flags.in_demo_data = False
	print(f"CDM demo data created for {len(patients)} patients.")


def remove_demo_data():
	"""Remove all demo data by deleting records with CDM-DEMO naming prefix."""
	doctypes = [
		"Care Coordinator Action", "Care Gap", "Complication Screening Tracker",
		"CDM Alert", "Medication Side Effect Log", "Medication Adherence Log",
		"Supplement Log", "Activity Log", "Meal Log",
		"Home Monitoring Entry", "Diet Plan",
		"Disease Goal", "CDM Care Plan",
		"Obesity Profile", "Diabetes Profile",
		"Disease Baseline Assessment", "Disease Enrollment",
	]

	for dt in doctypes:
		if not frappe.db.exists("DocType", dt):
			continue
		records = frappe.get_all(dt, filters={"name": ["like", f"{_DEMO_PREFIX}%"]})
		for r in records:
			frappe.delete_doc(dt, r.name, force=True, ignore_permissions=True)

	frappe.db.commit()
	print("CDM demo data removed.")


def _ensure_demo_patients() -> list[dict]:
	"""Ensure demo patients exist."""
	demo_patients = [
		{"patient_name": "Ahmed Khan", "sex": "Male", "dob": "1965-03-15"},
		{"patient_name": "Fatima Al-Rashid", "sex": "Female", "dob": "1972-08-22"},
		{"patient_name": "Omar Habib", "sex": "Male", "dob": "1980-11-03"},
	]

	patients = []
	for p in demo_patients:
		existing = frappe.db.get_value("Patient", {"patient_name": p["patient_name"]}, "name")
		if existing:
			patients.append({"name": existing, **p})
		else:
			doc = frappe.new_doc("Patient")
			doc.first_name = p["patient_name"].split()[0]
			doc.last_name = p["patient_name"].split()[-1] if len(p["patient_name"].split()) > 1 else ""
			doc.sex = p["sex"]
			doc.dob = p["dob"]
			doc.flags.ignore_permissions = True
			doc.insert()
			patients.append({"name": doc.name, **p})

	return patients


def _create_enrollments(patients: list[dict]) -> list[dict]:
	"""Create demo enrollments."""
	if not frappe.db.exists("DocType", "Disease Enrollment"):
		return []

	program_map = [
		("Diabetes", patients[0]),
		("Obesity", patients[1]),
		("Combined Metabolic", patients[2]),
	]

	enrollments = []
	for disease_type, patient in program_map:
		existing = frappe.db.exists(
			"Disease Enrollment",
			{"patient": patient["name"], "disease_type": disease_type, "program_status": "Active"},
		)
		if existing:
			enrollments.append({
				"name": existing,
				"patient": patient["name"],
				"disease_type": disease_type,
			})
			continue

		doc = frappe.new_doc("Disease Enrollment")
		doc.patient = patient["name"]
		doc.disease_type = disease_type
		doc.program_status = "Active"
		doc.enrollment_date = add_days(nowdate(), -90)
		doc.flags.ignore_permissions = True
		doc.insert()
		enrollments.append({
			"name": doc.name,
			"patient": patient["name"],
			"disease_type": disease_type,
		})

	return enrollments


def _create_profiles(enrollments: list[dict]) -> None:
	"""Create diabetes and obesity profiles for demo patients."""
	for e in enrollments:
		if e["disease_type"] in ("Diabetes", "Combined Metabolic"):
			if frappe.db.exists("DocType", "Diabetes Profile"):
				if not frappe.db.exists("Diabetes Profile", {"enrollment": e["name"], "status": "Active"}):
					doc = frappe.new_doc("Diabetes Profile")
					doc.patient = e["patient"]
					doc.enrollment = e["name"]
					doc.diabetes_type = "Type 2"
					doc.uses_insulin = 0
					doc.uses_smbg = 1
					doc.flags.ignore_permissions = True
					doc.insert()

		if e["disease_type"] in ("Obesity", "Combined Metabolic"):
			if frappe.db.exists("DocType", "Obesity Profile"):
				if not frappe.db.exists("Obesity Profile", {"enrollment": e["name"], "status": "Active"}):
					doc = frappe.new_doc("Obesity Profile")
					doc.patient = e["patient"]
					doc.enrollment = e["name"]
					doc.obesity_class = "Class I"
					doc.baseline_weight = 95.0
					doc.baseline_bmi = 32.5
					doc.flags.ignore_permissions = True
					doc.insert()


def _create_monitoring_entries(patients: list[dict], enrollments: list[dict]) -> None:
	"""Create sample monitoring entries."""
	if not frappe.db.exists("DocType", "Home Monitoring Entry") or not enrollments:
		return

	import random

	for i, e in enumerate(enrollments):
		for day_offset in range(0, 30, 3):
			doc = frappe.new_doc("Home Monitoring Entry")
			doc.patient = e["patient"]
			doc.enrollment = e["name"]
			doc.entry_type = "Fasting Glucose"
			doc.entry_source = "Patient"
			doc.recorded_at = add_days(now_datetime(), -(30 - day_offset))
			doc.numeric_value = round(random.uniform(90, 180), 1)
			doc.unit = "mg/dL"
			doc.is_patient_entered = 1
			doc.flags.ignore_permissions = True
			doc.insert()

		for day_offset in range(0, 30, 7):
			doc = frappe.new_doc("Home Monitoring Entry")
			doc.patient = e["patient"]
			doc.enrollment = e["name"]
			doc.entry_type = "Weight"
			doc.entry_source = "Clinician"
			doc.recorded_at = add_days(now_datetime(), -(30 - day_offset))
			doc.numeric_value = round(random.uniform(85, 100), 1)
			doc.unit = "kg"
			doc.flags.ignore_permissions = True
			doc.insert()


def _create_care_plans(enrollments: list[dict]) -> None:
	"""Create care plans for demo enrollments."""
	if not frappe.db.exists("DocType", "CDM Care Plan"):
		return

	for e in enrollments:
		if not frappe.db.exists("CDM Care Plan", {"enrollment": e["name"], "status": "Active"}):
			doc = frappe.new_doc("CDM Care Plan")
			doc.enrollment = e["name"]
			doc.patient = e["patient"]
			doc.status = "Active"
			doc.start_date = add_days(nowdate(), -85)
			doc.flags.ignore_permissions = True
			doc.insert()


def _create_alerts(patients: list[dict], enrollments: list[dict]) -> None:
	"""Create sample alerts."""
	if not frappe.db.exists("DocType", "CDM Alert") or not enrollments:
		return

	doc = frappe.new_doc("CDM Alert")
	doc.patient = enrollments[0]["patient"]
	doc.enrollment = enrollments[0]["name"]
	doc.alert_type = "Repeated High Fasting Glucose"
	doc.severity = "High"
	doc.status = "Open"
	doc.message = "3 high fasting glucose readings in the last 30 days."
	doc.identified_on = add_days(nowdate(), -2)
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_screenings(patients: list[dict], enrollments: list[dict]) -> None:
	"""Create sample screening trackers."""
	if not frappe.db.exists("DocType", "Complication Screening Tracker") or not enrollments:
		return

	screening_types = ["HbA1c Review", "Renal Screening", "Foot Exam"]
	for i, st in enumerate(screening_types):
		doc = frappe.new_doc("Complication Screening Tracker")
		doc.patient = enrollments[0]["patient"]
		doc.enrollment = enrollments[0]["name"]
		doc.screening_type = st
		doc.due_date = add_days(nowdate(), -10 + (i * 15))
		doc.status = "Due"
		doc.flags.ignore_permissions = True
		doc.insert()


def _create_care_gaps(patients: list[dict], enrollments: list[dict]) -> None:
	"""Create sample care gaps."""
	if not frappe.db.exists("DocType", "Care Gap") or not enrollments:
		return

	doc = frappe.new_doc("Care Gap")
	doc.patient = enrollments[0]["patient"]
	doc.enrollment = enrollments[0]["name"]
	doc.gap_type = "Lab Gap"
	doc.title = "Overdue HbA1c test"
	doc.severity = "High"
	doc.status = "Open"
	doc.identified_on = add_days(nowdate(), -5)
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_coordinator_actions(patients: list[dict], enrollments: list[dict]) -> None:
	"""Create sample coordinator actions."""
	if not frappe.db.exists("DocType", "Care Coordinator Action") or not enrollments:
		return

	doc = frappe.new_doc("Care Coordinator Action")
	doc.patient = enrollments[0]["patient"]
	doc.enrollment = enrollments[0]["name"]
	doc.action_type = "Contacted"
	doc.action_date = add_days(nowdate(), -1)
	doc.performed_by = "Administrator"
	doc.notes = "Called patient to remind about overdue HbA1c."
	doc.flags.ignore_permissions = True
	doc.insert()
