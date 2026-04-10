# User Role Management — Requirements

## Overview

Taskyn currently operates as a single-user system — the web UI has JWT authentication but no concept of ownership, teams, or permissions. All companies and projects are globally visible to any authenticated user. This spec introduces user role management: personal workspaces, team formation, project sharing, and role-based access control.

The core MCP server remains user-agnostic (it's a local single-user tool). RBAC is enforced exclusively at the web API layer, where user identity is available via JWT. This maintains a clean separation — the core Taskyn library handles PM logic, the web layer handles multi-tenancy.

Key constraint: Taskyn uses two SQLite databases — the core DB (companies, projects, nodes) and the web backend DB (users, auth). Membership and permission tables belong in the web backend DB, with the web API layer bridging user identity to core data access.

---

## User Stories

### URM-1: Personal Workspace

**As a** new user,
**I want** a personal workspace created automatically when I register,
**so that** I can start creating projects immediately without setup.

**Acceptance Criteria:**
- Registration creates a default company named "{name}'s Workspace" in the core DB
- A `company_members` record is created linking the user to this company with role `owner`
- The company has `type = personal` (distinguishing it from team companies)
- Users cannot delete their personal workspace
- The personal workspace is the default context for new projects

### URM-2: Project Ownership

**As a** user,
**I want** my projects to be associated with my account,
**so that** only I (and people I explicitly share with) can see and manage them.

**Acceptance Criteria:**
- Every project created through the web UI records the creating user as owner via `company_members` inheritance
- Projects under a personal workspace are visible only to the workspace owner
- Projects under a team workspace follow team membership rules (see URM-7)
- Existing projects (pre-migration) are assigned to the first registered user or a configurable admin user

### URM-3: User Profile Management

**As a** user,
**I want** to view and update my profile,
**so that** my identity is accurate across the system.

**Acceptance Criteria:**
- `GET /api/v1/auth/me` returns full user profile (id, email, name, created_at)
- `PATCH /api/v1/auth/me` allows updating the `name` field
- Email is read-only (email change requires verification — out of scope)
- Profile updates are reflected immediately across all UI components

### URM-4: Data Isolation

**As a** user,
**I want** to see only my own companies and projects by default,
**so that** the system respects privacy boundaries.

**Acceptance Criteria:**
- `GET /api/v1/companies` returns only companies where the user is a member
- `GET /api/v1/projects` returns only projects in companies the user has access to
- `GET /api/v1/nodes` filters to projects the user can access
- Direct access to a resource the user doesn't have permission for returns HTTP 403
- Dashboard, search, and activity endpoints all respect the same access boundaries

### URM-5: Team Creation

**As a** user,
**I want** to create a team,
**so that** I can collaborate with others on shared projects.

**Acceptance Criteria:**
- `POST /api/v1/companies` with `type = team` creates a team workspace
- The creating user is automatically added as `owner` in `company_members`
- Team companies have a human-readable name chosen by the creator
- A user can create multiple teams
- A user can be a member of multiple teams

### URM-6: Team Invitations

**As a** team owner or admin,
**I want** to invite users to my team by email,
**so that** they can access shared projects.

**Acceptance Criteria:**
- `POST /api/v1/companies/{id}/invitations` creates a pending invitation
- Invitation specifies the role the invitee will receive (admin, member)
- If the invitee already has an account, the invitation appears in their UI
- If the invitee doesn't have an account, the invitation is stored and applied on registration
- Invitations expire after 7 days
- Invitations can be revoked by the inviter or any team admin
- Duplicate invitations (same email, same company) are rejected

### URM-7: Team Roles

**As a** team owner,
**I want** team members to have defined roles,
**so that** permissions are clear and appropriate.

**Acceptance Criteria:**
- Three team roles: `owner`, `admin`, `member`
- **Owner**: Full control — manage members, all projects, delete team, transfer ownership
- **Admin**: Manage members (except owner), manage all projects, invite users
- **Member**: Access shared projects based on project-level permissions
- A team must have exactly one owner at all times
- Ownership can be transferred to another member (the original owner becomes admin)

### URM-8: Membership Management

**As a** team admin or owner,
**I want** to view and manage team members,
**so that** I can control who has access.

**Acceptance Criteria:**
- `GET /api/v1/companies/{id}/members` lists all members with roles
- `PATCH /api/v1/companies/{id}/members/{user_id}` changes a member's role
- `DELETE /api/v1/companies/{id}/members/{user_id}` removes a member
- Owners cannot be removed (must transfer ownership first)
- Users can leave a team voluntarily (except owners)
- Removing a member revokes all their project-level permissions in that team

### URM-9: Project Sharing

**As a** project owner or team admin,
**I want** to share a project with specific roles,
**so that** collaborators have the right level of access.

**Acceptance Criteria:**
- Team members inherit a default role on all projects in the team (configurable per team: `editor` or `viewer`)
- Project-level overrides can grant a team member a higher role on a specific project
- `POST /api/v1/projects/{id}/members` adds a project-level role override
- `DELETE /api/v1/projects/{id}/members/{user_id}` removes the override (reverts to team default)
- Project owners (team owner/admin) can manage project-level permissions

### URM-10: Permission Levels

**As a** system,
**I want** four permission levels on projects,
**so that** access control is granular and predictable.

**Acceptance Criteria:**
- **Owner**: Full control — delete project, manage sharing, all admin capabilities
- **Admin**: Manage project settings, create/edit/delete nodes, manage milestones, manage tags
- **Editor**: Create/edit nodes, log time, manage own time entries, add/remove tags
- **Viewer**: Read-only access — view project, nodes, dashboard, time reports
- Permission checks happen at the API route level via a reusable dependency
- Insufficient permissions return HTTP 403 with a descriptive error message

### URM-11: Access Enforcement

**As a** system,
**I want** every API endpoint to enforce permissions,
**so that** no unauthorized data access is possible.

**Acceptance Criteria:**
- A reusable `require_permission(project_id, min_role)` dependency is available for all routes
- Company-level routes check company membership
- Project-level routes check project access (company membership + project-level overrides)
- Node/edge/tag/time routes derive project access from the node's project_id
- Search results are filtered to accessible projects only
- The permission check is efficient (single query, cached per request)

### URM-12: MCP Boundary

**As a** developer using the MCP server directly (via Claude Code),
**I want** the MCP server to remain user-agnostic,
**so that** local single-user workflows are unaffected.

**Acceptance Criteria:**
- The MCP server (`src/taskyn/mcp/`) makes no changes for this spec
- All RBAC logic lives in `src/taskyn/web/backend/`
- The core library (`src/taskyn/core/`, `src/taskyn/graph/`, `src/taskyn/db/`) has no user/permission concepts
- The web API layer is the sole boundary where permissions are enforced

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `users` table (web backend DB) | Exists | id, email, password_hash, name, created_at |
| `companies` table (core DB) | Exists | No changes — workspace type tracked in `company_meta` (web backend DB) |
| `company_meta` table (web backend DB) | To be built | company_id, workspace_type, default_project_role, created_by |
| JWT auth (access + refresh) | Exists | No changes needed |
| `company_members` table (web backend DB) | To be built | user_id, company_id, role, joined_at |
| `project_members` table (web backend DB) | To be built | user_id, project_id, role, granted_at |
| `invitations` table (web backend DB) | To be built | id, company_id, inviter_id, invitee_email, role, status, created_at, expires_at |

---

## Configuration Summary

### Environment Variables

```
TASKYN_MIGRATION_ADMIN_EMAIL=<email of user who inherits pre-existing data during migration>
```

---

## Out of Scope

- Email verification and password reset flows
- OAuth/SSO providers (Google, GitHub)
- Real-time notifications when shared project changes (would need SSE — separate spec if ever needed)
- Fine-grained node-level permissions (permissions are at project level)
- Audit logging of permission changes
- Email delivery for invitations (invitations are in-app only for now)
- Cross-team project sharing (projects belong to one company/team)

---

## Open Questions

1. **Default team member role on projects**: Should new team members default to `editor` or `viewer` on existing projects? Leaning toward `editor` for smaller teams, but this could be team-configurable.
2. **Migration of existing data**: The first registered user inherits everything — is this acceptable, or should there be an admin setup flow?
