# Alcura Disease Management -- Documentation

This folder contains all project documentation for the Alcura Disease Management (CDM) Frappe app.

## Structure

| Directory | Contents |
|---|---|
| `architecture/` | Solution overview, domain model, integration points, security model, permissions matrix |
| `flows/` | User flow diagrams and step-by-step workflow descriptions |
| `llm-prompts/` | Prompts used for LLM-assisted development tasks |
| `doctypes/` | Documentation for each custom doctype |
| `reports/` | Documentation for reports, dashboards, and analytics |
| `api/` | API endpoint documentation |
| `decisions/` | Architecture Decision Records (ADRs) |
| `setup/` | Local development and deployment guides |
| `testing/` | Test strategy and coverage documentation |
| `release-notes/` | Release notes by version |

## Conventions

- All documentation is written in Markdown.
- Diagrams use Mermaid syntax where possible (rendered natively by GitHub / most Markdown viewers).
- Each feature added to the codebase must have corresponding documentation updates covering: business purpose, user flow, doctypes/fields, reports/pages, security impact, test coverage, and migration notes.
- ADRs follow the format: `ADR-NNN-short-title.md`.
