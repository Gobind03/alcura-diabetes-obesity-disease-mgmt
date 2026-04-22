# Local Development Setup

## Prerequisites

- Python >= 3.11
- Node.js >= 18
- MariaDB >= 10.6
- Redis >= 6
- A working Frappe bench (v16)

## Step 1: Set Up Bench (if not already done)

```bash
bench init frappe-bench --frappe-branch version-16
cd frappe-bench
```

## Step 2: Install Required Apps

```bash
bench get-app erpnext --branch version-16
bench get-app hrms --branch version-16
bench get-app healthcare --branch version-16
```

## Step 3: Create a Development Site

```bash
bench new-site dev.localhost \
    --mariadb-root-password your_password \
    --admin-password admin

bench --site dev.localhost install-app erpnext
bench --site dev.localhost install-app hrms
bench --site dev.localhost install-app healthcare
```

## Step 4: Install the CDM App

```bash
# Option A: Link from local path
bench get-app /path/to/alcura_diabetes_obesity_disease_mgmt

# Option B: Clone from git
# bench get-app https://github.com/Gobind03/alcura-diabetes-obesity-disease-mgmt.git --branch main

bench --site dev.localhost install-app alcura_diabetes_obesity_disease_mgmt
bench --site dev.localhost migrate
```

## Step 5: Start Development Server

```bash
bench start
```

The site will be available at `http://dev.localhost:8000`.

## Running Tests

```bash
# Via bench
bench --site dev.localhost run-tests --app alcura_diabetes_obesity_disease_mgmt

# Via pytest (from the app directory)
cd apps/alcura_diabetes_obesity_disease_mgmt
python -m pytest

# Run a specific test file
python -m pytest alcura_diabetes_obesity_disease_mgmt/tests/test_constants.py -v
```

## Code Quality

```bash
# Lint with ruff
ruff check alcura_diabetes_obesity_disease_mgmt/

# Format with ruff
ruff format alcura_diabetes_obesity_disease_mgmt/
```

## Loading Demo Data

```bash
bench --site dev.localhost execute \
    alcura_diabetes_obesity_disease_mgmt.setup.demo_data.create_demo_data
```

## Troubleshooting

- **Import errors after install**: Run `bench --site dev.localhost clear-cache` and `bench build`.
- **Missing Custom Fields**: Run `bench --site dev.localhost migrate` to trigger fixtures import.
- **Test site not found**: Ensure `test_site` exists or update `conftest.py` with your site name.
