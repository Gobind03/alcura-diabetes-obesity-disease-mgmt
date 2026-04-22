# API Documentation

This directory documents all whitelisted API endpoints exposed by the CDM app.

## API Design Principles

- All endpoints use `@frappe.whitelist(allow_guest=False)` unless explicitly justified.
- Endpoints follow RESTful naming where practical.
- Request/response payloads are documented with types.
- Portal-facing endpoints include patient identity verification.

## Planned API Modules

| Module | Path Prefix | Purpose |
|---|---|---|
| Enrollment | `chronic_disease_management.api.enrollment` | Enrollment CRUD, eligibility checks |
| Care Plan | `chronic_disease_management.api.care_plan` | Care plan retrieval, goal updates |
| Monitoring | `chronic_disease_management.api.monitoring` | Vitals submission, monitoring history |
| Portal | `chronic_disease_management.api.portal` | Patient portal data access |

## Documentation Template

Each endpoint document should cover:
- Method signature
- Authentication requirements
- Request parameters (with types and validation)
- Response format
- Error codes
- Example request/response
- Permission checks performed
