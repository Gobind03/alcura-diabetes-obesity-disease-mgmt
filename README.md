# Alcura Disease Management

A production-grade Frappe 16 app for longitudinal management of **Diabetes**, **Obesity**, and **Combined Metabolic Conditions**. Built as an extension layer over [Marley Health](https://github.com/frappe/health) (Frappe Healthcare), ERPNext 16, and HRMS 16.

## Architecture Principle

This app follows a **reuse-first** strategy:

- **Extends** existing Healthcare doctypes (`Patient`, `Patient Encounter`, `Vital Signs`, `Lab Test`, `Patient Appointment`, `Practitioner`) via Custom Fields, Property Setters, and hook-based event handlers.
- **Creates custom doctypes** only for domain-specific concepts that have no adequate representation in the base platform (e.g., Disease Enrollment, Care Plan, Protocol Template, Goal Tracking).
- **Never forks** core Frappe, ERPNext, or Marley Health code.

## Modules

| Module | Purpose |
|---|---|
| CDM Enrollment | Patient enrollment into disease management programs |
| CDM Care Plans | Individualized care plan creation and lifecycle |
| CDM Reviews | Periodic clinical reviews and follow-ups |
| CDM Monitoring | Patient self-monitoring, vitals tracking, alerts |
| CDM Dashboards | Clinician and program dashboards |
| CDM Reports | Script reports, query reports, analytics |
| CDM Patient Portal | Patient-facing portal pages and web forms |
| CDM Protocols | Evidence-based protocol templates and compliance |
| CDM Integrations | External system integrations and data exchange |
| CDM Shared | Cross-cutting utilities, shared child tables, lookups |

## Prerequisites

- **Frappe Bench** (v5.x) — [Bench installation guide](https://frappeframework.com/docs/user/en/installation)
- **Frappe** >= 16.0.0
- **ERPNext** >= 16.0.0
- **HRMS** >= 16.0.0
- **Marley Health** (Healthcare) >= 16.0.0
- **Python** >= 3.11
- **Node.js** >= 18
- **MariaDB** >= 10.6 or **PostgreSQL** >= 14
- **Redis** >= 6

## Installation

### 1. Install from Git (recommended)

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/Gobind03/alcura-diabetes-obesity-disease-mgmt.git

# Install the app on your site
bench --site your-site.localhost install-app alcura_diabetes_obesity_disease_mgmt

# Run migrations to set up doctypes, roles, and fixtures
bench --site your-site.localhost migrate

# (Optional) Restart bench to pick up all hooks
bench restart
```

### 2. Install from a local clone

```bash
# Clone the repo
git clone https://github.com/Gobind03/alcura-diabetes-obesity-disease-mgmt.git

# Get the app from the local path
bench get-app /path/to/alcura-diabetes-obesity-disease-mgmt

# Install and migrate
bench --site your-site.localhost install-app alcura_diabetes_obesity_disease_mgmt
bench --site your-site.localhost migrate
```

### 3. Verify Installation

After installation, verify the app is active:

```bash
bench --site your-site.localhost list-apps
```

You should see `alcura_diabetes_obesity_disease_mgmt` in the output. The **Alcura Disease Management** workspace will appear in the Frappe sidebar with quick access to all CDM modules.

## Post-Install Setup

1. **Navigate to the Workspace** — In Frappe Desk, open the sidebar and click **Alcura Disease Management** to access the main workspace.
2. **Configure Settings** — Go to `Disease Management Settings` to configure disease programs, thresholds, and defaults.
3. **Assign Roles** — Assign CDM-specific roles (`CDM Physician`, `CDM Care Coordinator`, `CDM Patient`, etc.) to your users via the User doctype.
4. **Install Demo Data** (development only):
   ```bash
   bench --site your-site.localhost execute alcura_diabetes_obesity_disease_mgmt.setup.demo_data.install
   ```

## Updating

```bash
cd ~/frappe-bench

# Pull latest changes
bench update --apps alcura_diabetes_obesity_disease_mgmt

# Or manually
cd apps/alcura_diabetes_obesity_disease_mgmt
git pull
cd ~/frappe-bench
bench --site your-site.localhost migrate
bench restart
```

## Uninstalling

```bash
bench --site your-site.localhost uninstall-app alcura_diabetes_obesity_disease_mgmt
bench remove-app alcura_diabetes_obesity_disease_mgmt
```

## Development

```bash
# Run tests
bench --site test_site run-tests --app alcura_diabetes_obesity_disease_mgmt

# Or with pytest directly
cd apps/alcura_diabetes_obesity_disease_mgmt
python -m pytest

# Run linter
cd apps/alcura_diabetes_obesity_disease_mgmt
ruff check .
ruff format --check .
```

## Documentation

Full documentation lives in [`docs/`](docs/README.md):

- [Solution Overview](docs/architecture/solution-overview.md)
- [Domain Model](docs/architecture/domain-model.md)
- [Integration Points](docs/architecture/integration-points.md)
- [Local Development Setup](docs/setup/local-development.md)
- [Architecture Decision Records](docs/decisions/)

## License

MIT
