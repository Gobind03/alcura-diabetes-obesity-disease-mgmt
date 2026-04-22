"""Comprehensive tests for CDM permission utilities, portal isolation, and audit logging."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Role-checking helpers
# ---------------------------------------------------------------------------

class TestIsCdmClinician:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_physician_is_clinician(self, mock_frappe):
		mock_frappe.session.user = "doc@example.com"
		mock_frappe.get_roles.return_value = ["CDM Physician", "System User"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_nurse_is_clinician(self, mock_frappe):
		mock_frappe.session.user = "nurse@example.com"
		mock_frappe.get_roles.return_value = ["CDM Nurse"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_coordinator_is_clinician(self, mock_frappe):
		mock_frappe.session.user = "coord@example.com"
		mock_frappe.get_roles.return_value = ["CDM Coordinator"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_dietitian_is_clinician(self, mock_frappe):
		mock_frappe.session.user = "diet@example.com"
		mock_frappe.get_roles.return_value = ["CDM Dietitian"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_is_not_clinician(self, mock_frappe):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is False

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_administrator_is_clinician(self, mock_frappe):
		mock_frappe.session.user = "Administrator"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_clinician
		assert is_cdm_clinician() is True


class TestIsCdmAdmin:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_admin_role(self, mock_frappe):
		mock_frappe.session.user = "admin@example.com"
		mock_frappe.get_roles.return_value = ["CDM Administrator"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_admin
		assert is_cdm_admin() is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_non_admin(self, mock_frappe):
		mock_frappe.session.user = "doc@example.com"
		mock_frappe.get_roles.return_value = ["CDM Physician"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import is_cdm_admin
		assert is_cdm_admin() is False


class TestGetPatientForUser:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_returns_patient_for_portal_user(self, mock_frappe):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.return_value = "PAT-001"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
		assert get_patient_for_user() == "PAT-001"

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_returns_none_for_administrator(self, mock_frappe):
		mock_frappe.session.user = "Administrator"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
		assert get_patient_for_user() is None

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_returns_none_for_guest(self, mock_frappe):
		mock_frappe.session.user = "Guest"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
		assert get_patient_for_user() is None

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_returns_none_when_no_patient_doctype(self, mock_frappe):
		mock_frappe.session.user = "user@example.com"
		mock_frappe.db.exists.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
		assert get_patient_for_user() is None


# ---------------------------------------------------------------------------
# Patient portal isolation
# ---------------------------------------------------------------------------

class TestGetAllowedPatients:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_admin_gets_none_unrestricted(self, mock_frappe):
		mock_frappe.session.user = "Administrator"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_allowed_patients
		assert get_allowed_patients() is None

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.is_cdm_admin")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.is_cdm_clinician")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_portal_patient_gets_own_id(self, mock_frappe, mock_clinician, mock_admin, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_admin.return_value = False
		mock_clinician.return_value = False
		mock_patient_for_user.return_value = "PAT-001"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_allowed_patients
		result = get_allowed_patients()
		assert result == ["PAT-001"]

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.is_cdm_admin")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.is_cdm_clinician")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_clinician_gets_none_unrestricted(self, mock_frappe, mock_clinician, mock_admin, mock_patient_for_user):
		mock_frappe.session.user = "doc@example.com"
		mock_frappe.get_roles.return_value = ["CDM Physician"]
		mock_admin.return_value = False
		mock_clinician.return_value = True
		mock_patient_for_user.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_allowed_patients
		result = get_allowed_patients()
		assert result is None


# ---------------------------------------------------------------------------
# Query conditions
# ---------------------------------------------------------------------------

class TestGetCdmQueryConditions:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_administrator_gets_empty(self, mock_frappe):
		mock_frappe.session.user = "Administrator"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_cdm_query_conditions
		assert get_cdm_query_conditions() == ""

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_cdm_admin_gets_empty(self, mock_frappe):
		mock_frappe.session.user = "admin@example.com"
		mock_frappe.get_roles.return_value = ["CDM Administrator"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_cdm_query_conditions
		assert get_cdm_query_conditions() == ""

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_clinician_gets_empty(self, mock_frappe):
		mock_frappe.session.user = "doc@example.com"
		mock_frappe.get_roles.return_value = ["CDM Physician"]

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_cdm_query_conditions
		assert get_cdm_query_conditions() == ""

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_gets_filtered(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-001"
		mock_frappe.db.escape.return_value = "'PAT-001'"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_cdm_query_conditions
		result = get_cdm_query_conditions()
		assert "patient" in result
		assert "PAT-001" in result

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_unknown_user_gets_blocked(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "unknown@example.com"
		mock_frappe.get_roles.return_value = []
		mock_patient_for_user.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_cdm_query_conditions
		result = get_cdm_query_conditions()
		assert result == "1=0"


# ---------------------------------------------------------------------------
# Has permission (document-level)
# ---------------------------------------------------------------------------

class TestHasCdmPermission:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_administrator_always_allowed(self, mock_frappe):
		mock_frappe.session.user = "Administrator"
		doc = MagicMock()

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc) is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_clinician_allowed(self, mock_frappe):
		mock_frappe.session.user = "doc@example.com"
		mock_frappe.get_roles.return_value = ["CDM Physician"]
		doc = MagicMock()

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc) is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_allowed_for_own_record(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-001"
		doc = MagicMock()
		doc.get.return_value = "PAT-001"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc) is True

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_denied_for_other_record(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-001"
		doc = MagicMock()
		doc.get.return_value = "PAT-002"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc) is False


class TestNoCrossPatientAccess:
	"""Simulate two patients and verify isolation."""

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_a_cannot_see_patient_b(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patientA@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-A"

		doc_b = MagicMock()
		doc_b.get.return_value = "PAT-B"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc_b) is False

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_patient_b_cannot_see_patient_a(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patientB@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-B"

		doc_a = MagicMock()
		doc_a.get.return_value = "PAT-A"

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import has_cdm_permission
		assert has_cdm_permission(doc_a) is False


# ---------------------------------------------------------------------------
# Portal access validation
# ---------------------------------------------------------------------------

class TestValidatePortalAccess:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_allows_own_record(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-001"
		mock_frappe.PermissionError = type("PermissionError", (Exception,), {})

		doc = {"patient": "PAT-001"}

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import validate_portal_access
		validate_portal_access(doc)

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.get_patient_for_user")
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions.frappe")
	def test_denies_other_record(self, mock_frappe, mock_patient_for_user):
		mock_frappe.session.user = "patient@example.com"
		mock_frappe.get_roles.return_value = ["CDM Patient"]
		mock_patient_for_user.return_value = "PAT-001"
		mock_frappe.PermissionError = type("PermissionError", (Exception,), {})
		mock_frappe.throw.side_effect = mock_frappe.PermissionError("denied")

		doc = {"patient": "PAT-002"}

		from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import validate_portal_access
		with pytest.raises(mock_frappe.PermissionError):
			validate_portal_access(doc)


# ---------------------------------------------------------------------------
# Role matrix
# ---------------------------------------------------------------------------

class TestRoleMatrix:
	def test_all_doctypes_have_entries(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import CDM_DOCTYPES, PERMISSION_MATRIX
		assert len(CDM_DOCTYPES) >= 7
		for dt in CDM_DOCTYPES:
			assert dt in PERMISSION_MATRIX

	def test_all_roles_are_valid(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import validate_permission_matrix
		issues = validate_permission_matrix()
		assert issues == {}, f"Matrix validation issues: {issues}"

	def test_get_permissions_for_doctype(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import get_permissions_for_doctype
		perms = get_permissions_for_doctype("Disease Enrollment")
		assert len(perms) >= 5
		roles = {p["role"] for p in perms}
		assert "CDM Administrator" in roles
		assert "CDM Patient" in roles

	def test_unknown_doctype_raises(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import get_permissions_for_doctype
		with pytest.raises(KeyError, match="not found"):
			get_permissions_for_doctype("Nonexistent DocType")

	def test_admin_has_full_crud_on_enrollment(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import PERMISSION_MATRIX
		admin_perms = PERMISSION_MATRIX["Disease Enrollment"]["CDM Administrator"]
		assert admin_perms["read"] == 1
		assert admin_perms["write"] == 1
		assert admin_perms["create"] == 1
		assert admin_perms["delete"] == 1
		assert admin_perms["submit"] == 1
		assert admin_perms["cancel"] == 1

	def test_patient_has_read_only_on_enrollment(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import PERMISSION_MATRIX
		patient_perms = PERMISSION_MATRIX["Disease Enrollment"]["CDM Patient"]
		assert patient_perms["read"] == 1
		assert patient_perms.get("write", 0) == 0
		assert patient_perms.get("create", 0) == 0

	def test_patient_can_create_monitoring_entries(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import PERMISSION_MATRIX
		patient_perms = PERMISSION_MATRIX["Monitoring Entry"]["CDM Patient"]
		assert patient_perms["read"] == 1
		assert patient_perms["create"] == 1

	def test_nurse_role_present_in_matrix(self):
		from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import PERMISSION_MATRIX
		nurse_present = any(
			"CDM Nurse" in roles
			for roles in PERMISSION_MATRIX.values()
		)
		assert nurse_present


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

class TestAuditLogging:
	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.audit.frappe")
	def test_log_status_change_creates_comment(self, mock_frappe):
		mock_frappe.session.user = "doc@example.com"
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc

		from alcura_diabetes_obesity_disease_mgmt.permissions.audit import log_status_change
		log_status_change(
			"Disease Enrollment", "ENR-001", "status", "Draft", "Active"
		)

		mock_frappe.get_doc.assert_called_once()
		call_args = mock_frappe.get_doc.call_args[0][0]
		assert call_args["doctype"] == "Comment"
		assert call_args["reference_doctype"] == "Disease Enrollment"
		assert call_args["reference_name"] == "ENR-001"
		assert "Draft" in call_args["content"]
		assert "Active" in call_args["content"]
		mock_doc.insert.assert_called_once_with(ignore_permissions=True)

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.audit.frappe")
	def test_log_critical_action_creates_comment(self, mock_frappe):
		mock_frappe.session.user = "admin@example.com"
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc

		from alcura_diabetes_obesity_disease_mgmt.permissions.audit import log_critical_action
		log_critical_action(
			"Protocol Override",
			"Skipped step 3 per physician decision",
			reference_doctype="CDM Care Plan",
			reference_name="CP-001",
		)

		mock_frappe.get_doc.assert_called_once()
		call_args = mock_frappe.get_doc.call_args[0][0]
		assert "Protocol Override" in call_args["content"]
		assert call_args["reference_doctype"] == "CDM Care Plan"

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.audit.frappe")
	def test_log_critical_action_with_dict_details(self, mock_frappe):
		mock_frappe.session.user = "admin@example.com"
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc

		from alcura_diabetes_obesity_disease_mgmt.permissions.audit import log_critical_action
		log_critical_action(
			"Alert Dismissed",
			{"alert_id": "ALT-001", "reason": "False positive"},
		)

		call_args = mock_frappe.get_doc.call_args[0][0]
		assert "Alert Dismissed" in call_args["content"]
		assert "ALT-001" in call_args["content"]

	@patch("alcura_diabetes_obesity_disease_mgmt.permissions.audit.frappe")
	def test_get_audit_trail(self, mock_frappe):
		mock_frappe.get_all.return_value = [
			{"content": "Status changed", "comment_by": "admin", "creation": "2026-04-22"},
		]

		from alcura_diabetes_obesity_disease_mgmt.permissions.audit import get_audit_trail
		result = get_audit_trail("Disease Enrollment", "ENR-001")
		assert len(result) == 1
		mock_frappe.get_all.assert_called_once()
