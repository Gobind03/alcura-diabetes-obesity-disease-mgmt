# ADR-008: Disease Review Sheet Replaces Periodic Review

## Status

Accepted

## Context

The initial architecture planned a "Periodic Review" doctype for scheduling and tracking clinical reviews. Service stubs (`ReviewService`) and hook configurations referenced this name, but the doctype JSON was never created.

Story 8 specifies a "Disease Review Sheet" with a much richer set of structured clinical fields: symptom review, medication adherence, side effects tracking, glycemic events, nutrition/activity adherence, anthropometric response, interim events, and clinical assessments.

## Decision

Create the doctype as **Disease Review Sheet** and update all existing references to "Periodic Review" across services, hooks, dashboard queries, and workspace configuration.

## Rationale

1. **Richer domain model**: The Disease Review Sheet captures structured clinical data far beyond what a simple "Periodic Review" with a summary field would support.

2. **No migration burden**: Since "Periodic Review" was never implemented as a doctype (only referenced in stubs), renaming incurs zero data migration cost.

3. **Clearer naming**: "Disease Review Sheet" better communicates the document's purpose as a structured clinical form rather than just a calendar event.

4. **Single concept**: Having both a "Periodic Review" and a "Disease Review Sheet" would create confusion about which to use. One doctype serves both scheduled reviews and encounter-initiated reviews via the `status` field (Scheduled vs Draft).

## Changes Made

- `hooks.py`: `Periodic Review` → `Disease Review Sheet` in `permission_query_conditions` and `has_permission`
- `services/review.py`: All `Periodic Review` references → `Disease Review Sheet`
- `services/dashboard.py`: Updated `get_program_summary` and `get_practitioner_workload` queries
- Workspace JSON: Updated shortcuts and links
- Constants: `REVIEW_STATUS_TRANSITIONS` updated to include "Draft" and "Cancelled" states

## Consequences

- The "Periodic Review" name no longer appears in the codebase
- Existing tests that mocked `Periodic Review` have been updated
- Future stories referencing scheduled reviews should use `Disease Review Sheet` with `status = Scheduled`
