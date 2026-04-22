# Test Strategy

## Overview

The CDM app uses **pytest** as its test runner, with Frappe-aware fixtures for database isolation. Tests are organized by category and co-located with the code they test where appropriate.

## Test Categories

### 1. Unit Tests

- Test pure Python logic in `services/`, `utils/`, `constants/`, `permissions/`.
- No database or Frappe runtime required for constant/utility tests.
- Located in `chronic_disease_management/tests/`.

### 2. Integration Tests

- Test DocType CRUD, workflow transitions, and service-layer logic that touches the database.
- Use `conftest.py` fixtures for site initialization and transaction rollback.
- Located in `chronic_disease_management/tests/` or co-located with doctypes.

### 3. Permission Tests

- Verify role-based access on each CDM doctype.
- Test that unauthorized roles cannot read/write/submit.
- Test portal isolation (patient A cannot see patient B's data).
- Located in `chronic_disease_management/tests/`.

### 4. API Tests

- Test whitelisted API endpoints with simulated HTTP calls.
- Verify authentication, input validation, and response format.
- Located in `chronic_disease_management/tests/`.

### 5. Report Smoke Tests

- Verify that each report executes without errors.
- Check that column definitions are valid.
- Located alongside report modules or in `chronic_disease_management/tests/`.

### 6. Portal Access Tests

- Test patient portal pages render correctly for CDM Patient role.
- Verify data isolation between patients.
- Located in `chronic_disease_management/tests/`.

## Test Infrastructure

### conftest.py

```python
@pytest.fixture(scope="session")
def site_setup():
    frappe.init(site="test_site")
    frappe.connect()
    yield
    frappe.destroy()

@pytest.fixture(autouse=True)
def rollback_db(site_setup):
    frappe.db.savepoint("before_test")
    yield
    frappe.db.rollback(save_point="before_test")
    frappe.clear_cache()
```

Every test runs inside a savepoint that is rolled back after the test, ensuring full isolation.

### Running Tests

```bash
# All tests
python -m pytest

# Specific file
python -m pytest chronic_disease_management/tests/test_constants.py -v

# With coverage
python -m pytest --cov=chronic_disease_management --cov-report=html
```

## Coverage Goals

- Constants and utilities: 100%
- Service layer: >= 80%
- DocType validation and workflows: >= 80%
- Permissions: >= 90%
- API endpoints: >= 80%
- Reports: smoke test coverage for all reports

## Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<behavior_under_test>`
