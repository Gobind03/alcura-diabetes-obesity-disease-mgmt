"""Tests for Disease Management Settings doctype (import-level and validation logic)."""

from __future__ import annotations

from pathlib import Path
import json


class TestSettingsDocTypeDefinition:
	"""Validate the doctype JSON is well-formed without needing a live site."""

	@staticmethod
	def _load_json():
		path = (
			Path(__file__).resolve().parent.parent
			/ "cdm_shared"
			/ "doctype"
			/ "disease_management_settings"
			/ "disease_management_settings.json"
		)
		return json.loads(path.read_text())

	def test_is_single_doctype(self):
		data = self._load_json()
		assert data["issingle"] == 1

	def test_module_is_cdm_shared(self):
		data = self._load_json()
		assert data["module"] == "CDM Shared"

	def test_has_expected_fields(self):
		data = self._load_json()
		field_names = {f["fieldname"] for f in data["fields"] if f["fieldtype"] not in ("Section Break", "Column Break")}
		expected = {
			"enabled_programs",
			"default_company",
			"diabetes_review_interval_days",
			"obesity_review_interval_days",
			"metabolic_review_interval_days",
			"missed_review_grace_days",
			"hba1c_critical_threshold",
			"hba1c_warning_threshold",
			"bmi_critical_threshold",
			"bmi_warning_threshold",
			"bp_systolic_critical",
			"bp_systolic_warning",
			"fbs_critical_high",
			"fbs_warning_high",
			"enable_protocol_engine",
			"auto_create_care_plan_on_enrollment",
			"auto_schedule_reviews",
			"enable_patient_portal",
			"allow_self_monitoring_entry",
			"allowed_self_entry_types",
			"show_care_plan_to_patient",
			"show_lab_results_to_patient",
		}
		assert expected.issubset(field_names), f"Missing fields: {expected - field_names}"

	def test_permissions_include_system_manager(self):
		data = self._load_json()
		roles = {p["role"] for p in data["permissions"]}
		assert "System Manager" in roles

	def test_permissions_include_cdm_admin(self):
		data = self._load_json()
		roles = {p["role"] for p in data["permissions"]}
		assert "CDM Administrator" in roles

	def test_track_changes_enabled(self):
		data = self._load_json()
		assert data.get("track_changes") == 1

	def test_review_interval_defaults(self):
		data = self._load_json()
		fields_by_name = {f["fieldname"]: f for f in data["fields"]}
		assert fields_by_name["diabetes_review_interval_days"].get("default") == "90"
		assert fields_by_name["obesity_review_interval_days"].get("default") == "60"
		assert fields_by_name["metabolic_review_interval_days"].get("default") == "90"

	def test_alert_threshold_defaults(self):
		data = self._load_json()
		fields_by_name = {f["fieldname"]: f for f in data["fields"]}
		assert fields_by_name["hba1c_critical_threshold"].get("default") == "9.0"
		assert fields_by_name["hba1c_warning_threshold"].get("default") == "7.5"
		assert fields_by_name["bmi_critical_threshold"].get("default") == "40.0"
		assert fields_by_name["bp_systolic_critical"].get("default") == "180"


class TestSettingsController:
	"""Test the controller class can be imported and has expected methods."""

	def test_controller_importable(self):
		from chronic_disease_management.cdm_shared.doctype.disease_management_settings.disease_management_settings import (
			DiseaseManagementSettings,
		)
		assert DiseaseManagementSettings is not None

	def test_controller_has_validate(self):
		from chronic_disease_management.cdm_shared.doctype.disease_management_settings.disease_management_settings import (
			DiseaseManagementSettings,
		)
		assert hasattr(DiseaseManagementSettings, "validate")

	def test_controller_has_helper_methods(self):
		from chronic_disease_management.cdm_shared.doctype.disease_management_settings.disease_management_settings import (
			DiseaseManagementSettings,
		)
		assert hasattr(DiseaseManagementSettings, "get_review_interval")
		assert hasattr(DiseaseManagementSettings, "is_program_enabled")
		assert hasattr(DiseaseManagementSettings, "get_enabled_program_list")
		assert hasattr(DiseaseManagementSettings, "get_allowed_self_entry_types")


class TestChildTableDefinitions:
	"""Validate child table JSON files."""

	@staticmethod
	def _load_child(name):
		path = (
			Path(__file__).resolve().parent.parent
			/ "cdm_shared"
			/ "doctype"
			/ name
			/ f"{name}.json"
		)
		return json.loads(path.read_text())

	def test_enabled_program_is_child_table(self):
		data = self._load_child("cdm_enabled_program")
		assert data["istable"] == 1
		assert data["module"] == "CDM Shared"

	def test_enabled_program_has_disease_type_field(self):
		data = self._load_child("cdm_enabled_program")
		field_names = [f["fieldname"] for f in data["fields"]]
		assert "disease_type" in field_names

	def test_allowed_self_entry_is_child_table(self):
		data = self._load_child("cdm_allowed_self_entry_type")
		assert data["istable"] == 1
		assert data["module"] == "CDM Shared"

	def test_allowed_self_entry_has_entry_type_field(self):
		data = self._load_child("cdm_allowed_self_entry_type")
		field_names = [f["fieldname"] for f in data["fields"]]
		assert "entry_type" in field_names
