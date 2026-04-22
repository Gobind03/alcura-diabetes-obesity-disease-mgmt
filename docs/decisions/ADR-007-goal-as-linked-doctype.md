# ADR-007: Disease Goal as Linked DocType (not Child Table)

## Status

Accepted

## Context

Story 7 requires a goal structure for care plans. The story offers two options:
- Child table (`Disease Goal` as `istable: 1` under CDM Care Plan)
- Linked doctype (`Disease Goal` as a standalone doctype linked via `care_plan` field)

Goals need to support:
- Individual status lifecycle (Not Started / In Progress / Achieved / Revised)
- Versioning with historical preservation
- Independent queryability for dashboards and trend reports
- Effective date and review date per goal
- Active/inactive tracking

## Decision

Implement Disease Goal as a **linked doctype** with a self-referential `supersedes` field for revision tracking.

## Rationale

1. **Individual lifecycle**: Child table rows share the parent document's save cycle. A linked doctype allows each goal to be independently created, updated, and status-tracked without modifying the parent care plan.

2. **Revision history**: The `supersedes` link creates a natural revision chain. When revising, the old goal is marked "Revised" and a new one is created pointing back to it. This avoids complex versioning tables or audit-log mining.

3. **Independent queryability**: Linked documents can be queried directly (e.g., "all HbA1c goals across patients with status In Progress") without loading full care plan documents. This is critical for population-level dashboards and reports.

4. **Portal readiness**: Individual goal documents can be independently exposed to patient portal views with fine-grained permission control.

5. **Performance**: Child tables with many rows slow down parent document loads. Linked documents are loaded on demand.

## Trade-offs

- **More complex form UX**: Goals don't appear inline in the care plan form. Mitigated by rendering `goals_html` summary and providing "Add Goal" action button.
- **Extra DB round trips**: Loading goals requires a separate query. Mitigated by the `goals_html` pre-rendered summary and batch-loading in the encounter context service.
- **Referential integrity**: Frappe doesn't enforce FK constraints on Link fields. Mitigated by `on_trash` guard on the care plan and goal refresh hooks.

## Consequences

- `CarePlanService.add_goal` creates linked `Disease Goal` docs instead of appending child rows
- Care plan form includes `goals_html` auto-rendered section
- Goal revision creates new documents rather than modifying existing ones
- Dashboard queries can directly filter `Disease Goal` without joins through care plan
