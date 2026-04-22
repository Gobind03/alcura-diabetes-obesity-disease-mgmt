# Chronic Disease Management

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

## Stack

- **Frappe** >= 16.0.0
- **ERPNext** >= 16.0.0
- **HRMS** >= 16.0.0
- **Marley Health** (Healthcare) >= 16.0.0

## Quick Start

```bash
# From your bench directory
bench get-app /path/to/chronic_disease_management
bench --site your-site install-app chronic_disease_management
bench --site your-site migrate
```

## Development

```bash
# Run tests
bench --site test_site run-tests --app chronic_disease_management

# Or with pytest directly
cd apps/chronic_disease_management
python -m pytest
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
