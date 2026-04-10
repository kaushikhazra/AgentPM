# Design Dry-Run Report #1

**Document**: `.claude/specs/user-role-management/design.md`
**Reviewed**: 2026-03-10

---

## Critical Gaps (must fix before implementation)

### [C1] Company without company_meta breaks permission resolution
- **Pass**: Pass 2 (Data Flow Trace)
- **What**: If a company exists in core DB without a corresponding `company_meta` row (created via MCP directly, or migration didn't run for some companies), the single-query resolution (Section 2.2) returns `NULL` for `default_project_role`. The `_resolve_role` function (Section 2.2) would call `ProjectRole(None)` when `company_role` is `"member"`, raising a `ValueError` crash.
- **Risk**: Any team member accessing a project in a company without `company_meta` crashes the API. Since MCP is user-agnostic (URM-12), any company created via MCP directly (e.g., from Claude Code) would trigger this.
- **Fix**: Add NULL handling in `_resolve_role` — if `default_project_role` is None, default to `ProjectRole.EDITOR`. Also add a defensive check in `check_project_access` that creates a `company_meta` row with defaults if one is missing (same self-healing pattern as personal workspace).

### [C2] Member removal doesn't cascade to project_members
- **Pass**: Pass 1 (Completeness Check)
- **What**: URM-8 AC states: "Removing a member revokes all their project-level permissions in that team." The design handles this for company deletion (Section 3.6: `delete_all_project_members_for_company`), but the `DELETE /companies/{id}/members/{user_id}` endpoint (Section 3.1) doesn't specify cascading deletion of the removed user's `project_members` rows for projects in that company.
- **Risk**: A removed team member retains project-level role overrides. If they're later re-invited with a lower role, the stale overrides could grant higher access than intended.
- **Fix**: Add to the member removal handler: after deleting from `company_members`, also delete all `project_members` rows where `user_id` matches AND `project_id` is in a project belonging to that company. Same function (`delete_all_project_members_for_company`) but scoped to one user.

### [C3] Invitation expiry not enforced on read
- **Pass**: Pass 4 (State Machine & Transitions)
- **What**: The `invitations` table has an `expires_at` column, and the accept flow checks it (Section 4.3: `if inv.expires_at < now`). However, `GET /invitations/mine` (Section 3.2) doesn't filter by expiry or lazily update expired invitations. Users would see expired invitations listed as "pending" with no ability to accept them.
- **Risk**: Confusing UX — invitee sees a "pending" invitation, clicks accept, gets "Invitation has expired" error. Also violates URM-6 AC "Invitations expire after 7 days" — they appear to persist indefinitely.
- **Fix**: In the `GET /invitations/mine` handler, either (a) filter `WHERE expires_at > datetime('now')`, or (b) lazily update expired invitations to `status = 'expired'` before returning results. Option (b) is better — it keeps the DB consistent.

---

## Warnings (should fix, may cause issues)

### [W1] Requirement/design mismatch on company type storage
- **Pass**: Pass 1 (Completeness Check)
- **What**: The requirement's Infrastructure Dependencies table says `companies` table "Exists — needs migration: Add `type` column (personal/team)." The design chose `company_meta.workspace_type` in the web backend DB instead (Decision D3), intentionally NOT modifying the core DB. The requirement and design disagree on where workspace type is stored.
- **Risk**: An implementer following the requirement table would modify the core DB schema, violating D1/D3/URM-12.
- **Suggestion**: Update requirement.md Infrastructure Dependencies to remove the "Add `type` column" note on `companies` and add `company_meta` table instead (matching the design).

### [W2] Transfer ownership lacks explicit transaction requirement
- **Pass**: Pass 4 (State Machine & Transitions)
- **What**: The transfer-ownership endpoint updates two rows: old owner → admin, new member → owner. The design doesn't specify this must be atomic (within a SQLite transaction). If interrupted between updates, the team could temporarily have zero or two owners.
- **Risk**: Data corruption under edge conditions (process crash mid-operation). SQLite handles this well in practice (single-writer), but the design should be explicit.
- **Suggestion**: Add to Section 3.1: "Transfer must execute both role changes in a single transaction."

### [W3] Request schemas don't validate role constraints
- **Pass**: Pass 3 (Interface Contract Validation)
- **What**: `UpdateMemberRole.role` accepts all `CompanyRole` values including `OWNER`. `CreateInvitation.role` also accepts `OWNER`. The API rejects these at the handler level (Error Handling table), but the schema lets them through to validation.
- **Risk**: Weak input validation — the handler must remember to check. If a new developer adds a route using these schemas, they might not add the constraint check.
- **Suggestion**: Use `Literal["admin", "member"]` in `UpdateMemberRole.role` and `CreateInvitation.role` instead of `CompanyRole`. This moves validation to the schema layer (fail-fast, self-documenting).

### [W4] Invitation race conditions on concurrent requests
- **Pass**: Pass 6 (Concurrency & Ordering)
- **What**: Duplicate invitation prevention and accept/revoke races rely on application-level SELECT-then-UPDATE checks. Two concurrent requests could both pass the "no duplicate pending" check and create two invitations. Similarly, concurrent accept + revoke could both succeed.
- **Risk**: Duplicate invitations for the same email, or an accepted invitation that was meant to be revoked.
- **Suggestion**: Use `UPDATE invitations SET status = 'accepted' WHERE id = ? AND status = 'pending' RETURNING *` for atomic state transitions. For duplicate prevention, use a unique partial index: `CREATE UNIQUE INDEX idx_invitations_pending ON invitations(company_id, invitee_email) WHERE status = 'pending'` (SQLite supports partial indexes).

### [W5] Inviting an existing company member not handled
- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: The design specifies error handling for self-invitation and duplicate pending invitations, but not for inviting an email that belongs to someone already a member of the company.
- **Risk**: Admin invites an email, invitation is created, invitee accepts, `create_company_member` either crashes (UNIQUE constraint on PK) or creates a duplicate row.
- **Suggestion**: Add validation in the create invitation handler: check if a user with that email is already a `company_members` entry for this company. Return 409 "User is already a team member."

### [W6] InvitationResponse denormalized fields need cross-DB joining
- **Pass**: Pass 2 (Data Flow Trace)
- **What**: `InvitationResponse` includes `company_name` (stored in core DB via MCP) and `inviter_name` (stored in web backend DB users table). The design doesn't specify how these denormalized fields are populated in the route handler.
- **Risk**: Implementer might miss these fields, returning empty strings, or might make N+1 MCP calls when listing invitations.
- **Suggestion**: Specify in the API contract: "Route handler fetches company_name via MCP `pm_get_company` and inviter_name via `get_user()`. For list endpoints, batch-fetch companies and users to avoid N+1."

### [W7] Invitation expiry duration not specified in design
- **Pass**: Pass 1 (Completeness Check)
- **What**: URM-6 AC says "Invitations expire after 7 days." The `CreateInvitation` schema has no expiry field, and the design doesn't specify that the backend computes `expires_at = now() + 7 days`.
- **Risk**: Implementer must guess the expiry duration or hardcode an arbitrary value.
- **Suggestion**: Add to Section 3.2 or the CreateInvitation handler: `expires_at = datetime.utcnow() + timedelta(days=7)`. Consider making the duration configurable via env var or company_meta.

---

## Observations (worth discussing)

### [O1] Default workspace for new project creation
URM-1 AC says "The personal workspace is the default context for new projects." The design doesn't specify a defaulting mechanism — `POST /projects` requires `company_id`. The frontend would need to pre-select the personal workspace when no company is chosen. This is a frontend design concern, appropriately deferred to Future Work.

### [O2] No per-request permission caching for multi-entity operations
URM-11 AC says "cached per request." The design uses plain functions (D5), not FastAPI dependencies, so there's no automatic per-request deduplication. For routes that check permissions on multiple entities (e.g., edges with source and target in different projects), the same company membership could be resolved twice. Not a performance problem at Taskyn's scale, but deviates from the requirement's "cached" language.

### [O3] Declined invitation is minor scope addition
The design adds `InvitationStatus.DECLINED` and `POST /invitations/{id}/decline`. The requirement only mentions revocation by the inviter. Declining by the invitee is a natural complement and good UX, but is not in the original user stories.

### [O4] MCP-direct operations can create cross-DB inconsistencies
Companies or projects created/deleted via MCP (bypassing web API) will have no `company_meta` or `company_members` tracking. This is the accepted MCP boundary trade-off (D6/URM-12). C1's fix (self-healing company_meta) partially mitigates this.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 3        | 7        | 4            |

**Verdict**: PASS WITH WARNINGS

The architecture is sound — two-DB model, permission resolution algorithm, API contracts, and data isolation strategy are well-designed. The 3 critical gaps are all fixable without architectural changes: C1 needs NULL handling in permission resolution, C2 needs a cascade on member removal, and C3 needs expiry filtering on invitation reads. The 7 warnings are schema/validation tightening and race condition hardening — important for production but don't block implementation planning.

Recommended: Fix C1-C3 and W1-W3 in the design document before proceeding to `/implement`. W4-W7 can be addressed during implementation.
