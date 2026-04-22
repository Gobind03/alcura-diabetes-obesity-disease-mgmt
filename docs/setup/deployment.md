# Deployment Guide

## Prerequisites

- A production Frappe 16 bench with ERPNext 16, HRMS 16, and Marley Health 16 installed.
- Database backups taken before deployment.

## Installation

```bash
bench get-app alcura_diabetes_obesity_disease_mgmt --branch main
bench --site your-site install-app alcura_diabetes_obesity_disease_mgmt
bench --site your-site migrate
```

## Updating

```bash
cd apps/alcura_diabetes_obesity_disease_mgmt
git pull origin main
bench --site your-site migrate
bench build
bench restart
```

## Migration Safety

- All patches in `patches.txt` are idempotent.
- Custom Fields are created via `after_install` and re-applied on `migrate` via fixtures.
- Roles are created if they do not already exist.
- No destructive DDL operations are performed in patches.

## Rollback

If the app needs to be removed:

```bash
bench --site your-site uninstall-app alcura_diabetes_obesity_disease_mgmt
```

This will:
1. Run `before_uninstall` to remove Custom Fields and Roles.
2. Drop CDM-specific database tables.

## Post-Deployment Checklist

- [ ] Verify CDM roles exist in Role list
- [ ] Verify Custom Fields appear on Patient, Patient Encounter, etc.
- [ ] Verify CDM workspace is visible in the desk sidebar
- [ ] Assign CDM roles to appropriate users
- [ ] Test portal access with a CDM Patient user
