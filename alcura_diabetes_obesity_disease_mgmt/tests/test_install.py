"""Smoke tests verifying the app is importable and metadata is correct."""


def test_hooks_importable():
	from alcura_diabetes_obesity_disease_mgmt import hooks

	assert hooks.app_name == "alcura_diabetes_obesity_disease_mgmt"
	assert hooks.app_title == "Alcura Disease Management"
	assert hooks.app_license == "MIT"


def test_version_defined():
	from alcura_diabetes_obesity_disease_mgmt import __version__

	assert __version__
	assert isinstance(__version__, str)
	parts = __version__.split(".")
	assert len(parts) == 3, "Version should be semver (major.minor.patch)"


def test_required_apps():
	from alcura_diabetes_obesity_disease_mgmt import hooks

	assert "frappe/erpnext" in hooks.required_apps
	assert "healthcare" in hooks.required_apps


def test_fixtures_defined():
	from alcura_diabetes_obesity_disease_mgmt import hooks

	assert isinstance(hooks.fixtures, list)
	assert len(hooks.fixtures) >= 2
	dts = {f["dt"] for f in hooks.fixtures}
	assert "Custom Field" in dts
	assert "Property Setter" in dts


def test_permission_hooks_defined():
	from alcura_diabetes_obesity_disease_mgmt import hooks

	assert isinstance(hooks.permission_query_conditions, dict)
	assert "Disease Enrollment" in hooks.permission_query_conditions
	assert isinstance(hooks.has_permission, dict)
	assert "Disease Enrollment" in hooks.has_permission


def test_modules_txt_readable():
	from pathlib import Path

	modules_path = Path(__file__).resolve().parent.parent / "modules.txt"
	assert modules_path.exists()
	content = modules_path.read_text().strip()
	lines = [line.strip() for line in content.splitlines() if line.strip()]
	assert len(lines) == 10


def test_patches_txt_readable():
	from pathlib import Path

	patches_path = Path(__file__).resolve().parent.parent / "patches.txt"
	assert patches_path.exists()
	content = patches_path.read_text()
	assert "[pre_model_sync]" in content
	assert "[post_model_sync]" in content


def test_roles_include_nurse():
	from alcura_diabetes_obesity_disease_mgmt.constants.roles import ALL_CDM_ROLES

	assert "CDM Nurse" in ALL_CDM_ROLES
	assert len(ALL_CDM_ROLES) >= 6
