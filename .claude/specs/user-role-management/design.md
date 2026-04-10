# User Role Management — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Membership tables in web backend DB, not core DB | URM-12: MCP server stays user-agnostic. Core library has no user/permission concepts. |
| D2 | Company = workspace (personal or team) | URM-1, URM-5: Avoids a new entity. Companies already represent organizational containers. |
| D3 | `company_meta` table tracks workspace type and default project role | Keeps core DB `companies` table unchanged. Web-specific metadata stays in web backend DB. |
| D4 | Company role → project role mapping (owner/admin → admin, member → default) | URM-7, URM-9: Simple hierarchy. Overrides only upgrade, never downgrade. |
| D5 | Plain utility functions for permission checks, not FastAPI dependencies | Explicit call sites are easier to audit. No hidden dependency injection magic for security-critical code. |
| D6 | RBAC enforced at web API layer only | URM-12: MCP is a local single-user tool. The web API is the multi-user boundary. |
| D7 | Personal workspace auto-created on registration | URM-1: Zero-setup onboarding. Self-healing if creation fails (retried on next API call). |
| D8 | Invitations are in-app only (no email delivery) | Out of scope per requirements. Invitations appear in the invitee's UI. |
| D9 | Default team member project role is `editor`, configurable per team | URM-9: Open question resolved — `editor` is the sensible default for small collaborative teams. |
| D10 | Existing data migrated to first registered user (or `TASKYN_MIGRATION_ADMIN_EMAIL`) | URM-2: One-time startup migration. Non-destructive. Runs only when `company_meta` is empty. |
| D11 | Self-healing `company_meta` for MCP-created companies | Dryrun C1: Companies created via MCP (bypassing web API) have no `company_meta`. Permission resolution handles this gracefully with defaults. |
| D12 | Atomic invitation state transitions via `UPDATE...WHERE status='pending'` | Dryrun W4: Prevents race conditions on concurrent accept/revoke or duplicate creation. |

---

## 1. Data Model

### 1.1 New Enums

_Location: `src/taskyn/web/backend/auth/enums.py`_

```python
from enum import Enum

class CompanyRole(str, Enum):
    """Role within a company/team. Hierarchy: owner > admin > member."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class ProjectRole(str, Enum):
    """Effective role on a project. Hierarchy: admin > editor > viewer."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"
    EXPIRED = "expired"

# Numeric levels for comparison
COMPANY_ROLE_LEVEL = {
    CompanyRole.MEMBER: 1,
    CompanyRole.ADMIN: 2,
    CompanyRole.OWNER: 3,
}

PROJECT_ROLE_LEVEL = {
    ProjectRole.VIEWER: 1,
    ProjectRole.EDITOR: 2,
    ProjectRole.ADMIN: 3,
}
```

### 1.2 New Tables (Web Backend DB)

All tables live in the web backend SQLite database alongside the existing `users` table. They reference `company_id` and `project_id` from the core DB by value (no foreign key constraint across databases).

```sql
-- Workspace metadata for companies (personal vs team, settings)
CREATE TABLE IF NOT EXISTS company_meta (
    company_id   TEXT PRIMARY KEY,
    workspace_type TEXT NOT NULL DEFAULT 'team'
        CHECK (workspace_type IN ('personal', 'team')),
    default_project_role TEXT NOT NULL DEFAULT 'editor'
        CHECK (default_project_role IN ('editor', 'viewer')),
    created_by   TEXT NOT NULL
);

-- Company membership: links users to companies with roles
CREATE TABLE IF NOT EXISTS company_members (
    user_id      TEXT NOT NULL,
    company_id   TEXT NOT NULL,
    role         TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    joined_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, company_id)
);
CREATE INDEX IF NOT EXISTS idx_company_members_company
    ON company_members(company_id);

-- Project-level role overrides (upgrades only)
CREATE TABLE IF NOT EXISTS project_members (
    user_id      TEXT NOT NULL,
    project_id   TEXT NOT NULL,
    role         TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    granted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, project_id)
);
CREATE INDEX IF NOT EXISTS idx_project_members_project
    ON project_members(project_id);

-- Team invitations
CREATE TABLE IF NOT EXISTS invitations (
    id            TEXT PRIMARY KEY,
    company_id    TEXT NOT NULL,
    inviter_id    TEXT NOT NULL,
    invitee_email TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    status        TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined', 'revoked', 'expired')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at    TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_invitations_email
    ON invitations(invitee_email);
CREATE INDEX IF NOT EXISTS idx_invitations_company_status
    ON invitations(company_id, status);
-- D12: Prevent duplicate pending invitations at DB level
CREATE UNIQUE INDEX IF NOT EXISTS idx_invitations_pending_unique
    ON invitations(company_id, invitee_email) WHERE status = 'pending';
```

**Atomic invitation state transitions (D12):** All status changes use `UPDATE ... WHERE status = 'pending' RETURNING *` rather than SELECT-then-UPDATE, preventing race conditions on concurrent accept/revoke/expire operations. If the `UPDATE` returns no rows, the invitation was already processed by a concurrent request.

### 1.3 Pydantic Models

_Location: `src/taskyn/web/backend/auth/membership.py`_

```python
from pydantic import BaseModel
from .enums import CompanyRole, ProjectRole, InvitationStatus

class CompanyMember(BaseModel):
    user_id: str
    company_id: str
    role: CompanyRole
    joined_at: str

class CompanyMetaRecord(BaseModel):
    company_id: str
    workspace_type: str  # "personal" or "team"
    default_project_role: ProjectRole
    created_by: str

class ProjectMember(BaseModel):
    user_id: str
    project_id: str
    role: ProjectRole
    granted_at: str

class Invitation(BaseModel):
    id: str
    company_id: str
    inviter_id: str
    invitee_email: str
    role: CompanyRole
    status: InvitationStatus
    created_at: str
    expires_at: str

class ResolvedPermission(BaseModel):
    """Result of permission resolution for a user on a project."""
    user_id: str
    project_id: str
    company_id: str
    effective_role: ProjectRole
```

---

## 2. Permission Resolution

### 2.1 Algorithm

For a given `(user_id, project_id)`, resolve the effective project role:

```
1. Get project → extract company_id (MCP call)
2. Look up company_members WHERE user_id AND company_id
   → If not found: NO ACCESS (403)
3. Map company role to base project role:
   - owner  → admin
   - admin  → admin
   - member → company_meta.default_project_role (editor or viewer)
4. Look up project_members WHERE user_id AND project_id
   → If found AND override > base: use override
   → Otherwise: use base
5. Return effective role
```

_Why: URM-9 says overrides can only upgrade. URM-7 says owner/admin get full project access. URM-10 defines the four-tier model._

### 2.2 Single-Query Resolution

```sql
SELECT
    cm.role         AS company_role,
    pm.role         AS project_override,
    cs.default_project_role
FROM company_members cm
LEFT JOIN project_members pm
    ON pm.user_id = cm.user_id AND pm.project_id = :project_id
LEFT JOIN company_meta cs
    ON cs.company_id = cm.company_id
WHERE cm.user_id = :user_id AND cm.company_id = :company_id
```

Python resolves the effective role from the query result:

```python
def _resolve_role(
    company_role: str,
    default_project_role: str | None,
    project_override: str | None,
) -> ProjectRole:
    # Map company role to base project role
    if company_role in ("owner", "admin"):
        base = ProjectRole.ADMIN
    else:
        # D11: default_project_role may be None if company_meta is missing
        # (company created via MCP directly). Default to EDITOR.
        base = ProjectRole(default_project_role) if default_project_role else ProjectRole.EDITOR

    # Apply override if it upgrades
    if project_override:
        override = ProjectRole(project_override)
        if PROJECT_ROLE_LEVEL[override] > PROJECT_ROLE_LEVEL[base]:
            return override

    return base
```

### 2.3 Enforcement Utilities

_Location: `src/taskyn/web/backend/auth/rbac.py`_

```python
async def check_company_access(
    user_id: str,
    company_id: str,
    min_role: CompanyRole,
) -> CompanyMember:
    """Verify user has at least min_role on company. Raises 403."""
    member = get_company_member(user_id, company_id)
    if not member or COMPANY_ROLE_LEVEL[member.role] < COMPANY_ROLE_LEVEL[min_role]:
        raise HTTPException(403, f"Requires '{min_role.value}' role on this team")
    return member


async def check_project_access(
    user_id: str,
    project_id: str,
    min_role: ProjectRole,
    *,
    mcp_client,
) -> ResolvedPermission:
    """Resolve effective role and verify minimum. Raises 403."""
    # Get company_id from project (MCP call)
    project = await call_tool(mcp_client, "pm_get_project", project_id=project_id)
    company_id = project["company_id"]

    # D11: Ensure company_meta exists (self-healing for MCP-created companies)
    ensure_company_meta(company_id)

    # Single-query resolution
    role = resolve_project_role(user_id, project_id, company_id)
    if not role or PROJECT_ROLE_LEVEL[role] < PROJECT_ROLE_LEVEL[min_role]:
        raise HTTPException(403, f"Requires '{min_role.value}' role on this project")

    return ResolvedPermission(
        user_id=user_id,
        project_id=project_id,
        company_id=company_id,
        effective_role=role,
    )


def ensure_company_meta(company_id: str) -> None:
    """Create company_meta with defaults if missing. Idempotent."""
    existing = get_company_meta(company_id)
    if existing:
        return
    create_company_meta(company_id, workspace_type="team",
                        default_project_role="editor", created_by="system")


def get_accessible_company_ids(user_id: str) -> set[str]:
    """Return all company IDs where user is a member."""
    rows = db_query(
        "SELECT company_id FROM company_members WHERE user_id = ?",
        (user_id,),
    )
    return {r["company_id"] for r in rows}
```

_Why D5: These are plain functions called explicitly in route handlers. No hidden dependency injection — every permission check is visible at the call site._

### 2.4 Route Integration Pattern

Every existing route handler adds a permission check. Pattern:

```python
# Before (current — no access check)
@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    mcp: ... = Depends(get_mcp_client),
):
    return await call_mcp_tool(mcp, "pm_get_project", project_id=project_id)

# After (with access check)
@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    mcp: ... = Depends(get_mcp_client),
):
    await check_project_access(current_user.id, project_id, ProjectRole.VIEWER, mcp_client=mcp)
    return await call_mcp_tool(mcp, "pm_get_project", project_id=project_id)
```

For list endpoints:

```python
@router.get("/projects")
async def list_projects(
    current_user: User = Depends(get_current_user),
    mcp: ... = Depends(get_mcp_client),
    company_id: str | None = None,
    ...
):
    accessible = get_accessible_company_ids(current_user.id)

    # If company_id filter provided, verify access
    if company_id:
        if company_id not in accessible:
            raise HTTPException(403, "Not a member of this team")
        result = await call_mcp_tool(mcp, "pm_list_projects", company_id=company_id, ...)
    else:
        # Get all, filter by accessible companies
        result = await call_mcp_tool(mcp, "pm_list_projects", ...)
        result = [p for p in result if p["company_id"] in accessible]

    return result
```

### 2.5 Permission Matrix

| Action | Min Company Role | Min Project Role |
|--------|-----------------|-----------------|
| View company | member | — |
| Create company (team) | — (any user) | — |
| Delete company | owner | — |
| Manage company members | admin | — |
| Transfer ownership | owner | — |
| View project | member | viewer |
| Create project | member | — |
| Delete project | admin | — |
| Manage project members | admin | admin |
| View nodes/milestones/tags | member | viewer |
| Create/edit nodes | member | editor |
| Delete nodes | member | admin |
| Time tracking (start/stop/log) | member | editor |
| View time entries | member | viewer |
| Search/dashboard | member | viewer (filtered) |

---

## 3. API Contracts

### 3.1 Company Members

```
GET    /api/v1/companies/{company_id}/members
       Permission: company member
       Response: [CompanyMemberResponse]

PATCH  /api/v1/companies/{company_id}/members/{user_id}
       Permission: company admin+
       Body: { "role": "admin" | "member" }
       Constraint: Cannot change owner's role
       Response: CompanyMemberResponse

DELETE /api/v1/companies/{company_id}/members/{user_id}
       Permission: company admin+
       Constraint: Cannot remove owner
       Side effect: Deletes user's project_members rows for all projects in this company (URM-8)
       Response: 204

POST   /api/v1/companies/{company_id}/leave
       Permission: company member (not owner)
       Side effect: Deletes user's project_members rows for all projects in this company (URM-8)
       Response: 204

POST   /api/v1/companies/{company_id}/transfer-ownership
       Permission: company owner
       Body: { "new_owner_id": "..." }
       Constraint: new_owner must be existing member
       Behavior: In a single transaction: set new_owner role to 'owner',
                 set current owner role to 'admin'. Atomic — no intermediate state.
       Response: CompanyMemberResponse
```

### 3.2 Invitations

```
POST   /api/v1/companies/{company_id}/invitations
       Permission: company admin+
       Body: { "email": "...", "role": "admin" | "member" }
       Constraints: No self-invite, no duplicate pending, no existing member, valid role
       Behavior: Sets expires_at = now() + 7 days.
       Response: InvitationResponse (201)

GET    /api/v1/companies/{company_id}/invitations
       Permission: company admin+
       Response: [InvitationResponse]

DELETE /api/v1/companies/{company_id}/invitations/{invitation_id}
       Permission: company admin+
       Constraint: Only pending invitations can be revoked
       Response: 204

GET    /api/v1/invitations/mine
       Permission: any authenticated user
       Behavior: Lazily expires invitations where expires_at < now() before returning.
                 Returns only pending, non-expired invitations enriched with company_name.
       Response: [InvitationResponse]

POST   /api/v1/invitations/{invitation_id}/accept
       Permission: invitee (email matches current user)
       Constraint: Must be pending and not expired
       Response: CompanyMemberResponse

POST   /api/v1/invitations/{invitation_id}/decline
       Permission: invitee
       Response: 204
```

### 3.3 Project Members

```
GET    /api/v1/projects/{project_id}/members
       Permission: project admin+
       Response: [ProjectMemberResponse] (includes effective_role)

POST   /api/v1/projects/{project_id}/members
       Permission: project admin+
       Body: { "user_id": "...", "role": "admin" | "editor" | "viewer" }
       Constraint: user must be company member
       Response: ProjectMemberResponse (201)

DELETE /api/v1/projects/{project_id}/members/{user_id}
       Permission: project admin+
       Response: 204 (reverts to team default)
```

### 3.4 Profile Update

```
PATCH  /api/v1/auth/me
       Permission: any authenticated user
       Body: { "name": "..." }
       Response: User
```

### 3.5 Request/Response Schemas

_Location: `src/taskyn/web/backend/schemas/members.py`_

```python
from typing import Literal
from pydantic import BaseModel, EmailStr, Field
from ..auth.enums import CompanyRole, ProjectRole, InvitationStatus

class CompanyMemberResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: CompanyRole
    joined_at: str

class UpdateMemberRole(BaseModel):
    role: Literal["admin", "member"]  # owner excluded — use transfer-ownership

class TransferOwnership(BaseModel):
    new_owner_id: str

class CreateInvitation(BaseModel):
    email: EmailStr
    role: Literal["admin", "member"]  # owner excluded — validated at schema level

class InvitationResponse(BaseModel):
    """Denormalized response. Route handler fetches company_name via MCP
    pm_get_company and inviter_name via get_user(). For list endpoints,
    batch-fetch companies and users to avoid N+1."""
    id: str
    company_id: str
    company_name: str   # from core DB (MCP pm_get_company)
    inviter_name: str   # from web DB (get_user)
    invitee_email: str
    role: CompanyRole
    status: InvitationStatus
    created_at: str
    expires_at: str

class ProjectMemberResponse(BaseModel):
    user_id: str
    email: str
    name: str
    effective_role: ProjectRole
    has_override: bool
    override_role: ProjectRole | None = None

class SetProjectRole(BaseModel):
    user_id: str
    role: ProjectRole

class UpdateProfile(BaseModel):
    name: str = Field(min_length=1, max_length=255)
```

### 3.6 Modified Company Endpoints

`POST /api/v1/companies` gains automatic membership tracking:

```python
@router.post("/companies", status_code=201)
async def create_company(
    body: CompanyCreate,
    current_user: User = Depends(get_current_user),
    mcp: ... = Depends(get_mcp_client),
):
    # 1. Create in core DB via MCP
    company = await call_mcp_tool(mcp, "pm_create_company", ...)

    # 2. Create web backend records
    create_company_meta(company["id"], workspace_type="team", created_by=current_user.id)
    create_company_member(current_user.id, company["id"], CompanyRole.OWNER)

    return company
```

`DELETE /api/v1/companies/{company_id}` adds ownership check:

```python
@router.delete("/companies/{company_id}", status_code=204)
async def delete_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    mcp: ... = Depends(get_mcp_client),
):
    # Check personal workspace
    meta = get_company_meta(company_id)
    if meta and meta.workspace_type == "personal":
        raise HTTPException(400, "Cannot delete personal workspace")

    # Check owner role
    await check_company_access(current_user.id, company_id, CompanyRole.OWNER)

    # Delete core + web backend records
    await call_mcp_tool(mcp, "pm_delete_company", company_id=company_id)
    delete_company_meta(company_id)
    delete_all_company_members(company_id)
    delete_all_project_members_for_company(company_id, mcp)
    delete_all_invitations_for_company(company_id)
```

---

## 4. Registration Flow

### 4.1 Updated Registration Sequence

```
User                    FastAPI                 Web DB              MCP (Core DB)
 │                        │                       │                     │
 │─POST /auth/register──→│                       │                     │
 │                        │──create_user────────→│                     │
 │                        │                       │──user row──→       │
 │                        │──pm_create_company─────────────────────────→│
 │                        │                       │          ←─company─│
 │                        │──create_company_meta→│                     │
 │                        │  (personal, editor)   │                     │
 │                        │──create_company_member→│                    │
 │                        │  (owner)              │                     │
 │                        │──check_pending_invites→│                    │
 │                        │  (auto-accept)        │                     │
 │                        │←─────────────────────│                     │
 │←──201 success─────────│                       │                     │
```

### 4.2 Self-Healing Workspace

If personal workspace creation fails during registration (MCP unavailable, etc.):

```python
async def ensure_personal_workspace(user: User, mcp_client) -> str:
    """Ensure user has a personal workspace. Creates one if missing."""
    meta = get_personal_workspace(user.id)
    if meta:
        return meta.company_id

    # Create personal workspace
    company = await call_tool(mcp_client, "pm_create_company",
        name=f"{user.name}'s Workspace")
    create_company_meta(company["id"], "personal", "editor", user.id)
    create_company_member(user.id, company["id"], CompanyRole.OWNER)
    return company["id"]
```

Called from:
- Registration flow (primary)
- `GET /api/v1/companies` (self-healing fallback — if user has zero memberships)

_Why D7: Zero-setup onboarding. Self-healing pattern handles partial failures gracefully without transactions across two databases._

### 4.3 Invitation Auto-Accept on Registration

```python
async def auto_accept_pending_invitations(user: User):
    """Accept all pending invitations for this user's email."""
    invitations = get_pending_invitations_by_email(user.email)
    now = datetime.utcnow()

    for inv in invitations:
        if inv.expires_at < now:
            update_invitation_status(inv.id, InvitationStatus.EXPIRED)
            continue
        create_company_member(user.id, inv.company_id, inv.role)
        update_invitation_status(inv.id, InvitationStatus.ACCEPTED)
```

---

## 5. Data Isolation

### 5.1 Route Filtering Strategy

Every route that returns data must filter by user access. Three patterns:

**Pattern A — Company-scoped routes** (companies, company stats):
```python
accessible = get_accessible_company_ids(current_user.id)
# Filter results to accessible companies only
```

**Pattern B — Project-scoped routes** (projects, nodes, milestones, tags, time entries, timer):
```python
# For detail: check_project_access(user.id, project_id, min_role)
# For list: get accessible company_ids, filter by company membership
```

**Pattern C — Cross-cutting routes** (dashboard, search, activity):
```python
accessible = get_accessible_company_ids(current_user.id)
# Pass to MCP as filter, or filter results post-hoc
```

### 5.2 Existing Route Modifications

| Route File | Change |
|-----------|--------|
| `companies.py` | GET list: filter by membership. GET detail: check membership. POST: create meta+member. DELETE: check owner + not personal. |
| `projects.py` | GET list: filter by accessible companies. GET detail: check access (viewer). POST: check company membership. DELETE: check access (admin). |
| `nodes.py` | GET list: filter by accessible projects. GET detail: check project access (viewer). POST/PATCH: check access (editor). DELETE: check access (admin). |
| `edges.py` | Check project access on source node. Both nodes must be in accessible projects. |
| `milestones.py` | Same pattern as projects — check project access per operation. |
| `tags.py` | Node-based — check project access via node's project_id. |
| `timer.py` | Check project access (editor) for start/stop. Viewer for status. |
| `time_entries.py` | Check project access — viewer for read, editor for write. |
| `dashboard.py` | Filter all data by accessible projects. |
| `search.py` | Filter search results by accessible projects. |
| `activity.py` | Filter activity by accessible entities. |

---

## 6. Migration Strategy

### 6.1 One-Time Data Migration

Runs during app lifespan startup, only when `company_meta` table is empty but companies exist:

```python
async def migrate_existing_data(mcp_client):
    """Assign existing companies to admin user. Idempotent."""
    if count_company_meta_rows() > 0:
        return  # Already migrated

    companies = await call_tool(mcp_client, "pm_list_companies")
    if not companies:
        return  # No data to migrate

    # Find admin user
    admin_email = os.getenv("TASKYN_MIGRATION_ADMIN_EMAIL")
    admin = get_user_by_email(admin_email) if admin_email else None
    if not admin:
        admin = get_first_registered_user()
    if not admin:
        logger.warning("No users found — skipping migration")
        return

    for company in companies:
        create_company_meta(company["id"], "team", "editor", admin.id)
        create_company_member(admin.id, company["id"], CompanyRole.OWNER)

    logger.info("Migrated %d companies to user %s", len(companies), admin.email)
```

### 6.2 Schema Initialization

Table creation SQL runs during web backend auth initialization (same pattern as existing `users` table creation in `users.py`). The `_initialized` flag guards against repeated execution.

---

## Error Handling

| Scenario | HTTP Code | Error Message |
|----------|-----------|---------------|
| Not a company member | 403 | "Requires 'member' role on this team" |
| Insufficient project role | 403 | "Requires 'editor' role on this project" |
| Delete personal workspace | 400 | "Cannot delete personal workspace" |
| Remove team owner | 400 | "Cannot remove team owner. Transfer ownership first" |
| Change owner role | 400 | "Cannot change owner role. Transfer ownership first" |
| Owner tries to leave | 400 | "Owner cannot leave. Transfer ownership first" |
| Duplicate pending invitation | 409 | "Invitation already pending for this email" |
| Self-invitation | 400 | "Cannot invite yourself" |
| Accept expired invitation | 410 | "Invitation has expired" |
| Accept non-pending invitation | 400 | "Invitation is not pending" |
| Transfer to non-member | 400 | "New owner must be an existing team member" |
| Set override to owner role | 400 | "Cannot set 'owner' as project role. Owner is a team-level role" |
| Invite with owner role | 400 | "Cannot invite as owner. Use transfer ownership instead" |
| Invite existing member | 409 | "User is already a team member" |

---

## Files Changed

| File | Change |
|------|--------|
| `src/taskyn/web/backend/auth/enums.py` | **NEW** — CompanyRole, ProjectRole, InvitationStatus enums with level mappings |
| `src/taskyn/web/backend/auth/membership.py` | **NEW** — DB functions for company_members, project_members, company_meta, invitations CRUD |
| `src/taskyn/web/backend/auth/rbac.py` | **NEW** — Permission resolution, check_company_access, check_project_access, get_accessible_company_ids |
| `src/taskyn/web/backend/auth/users.py` | Add schema init for new tables (company_meta, company_members, project_members, invitations) |
| `src/taskyn/web/backend/auth/__init__.py` | Export new modules |
| `src/taskyn/web/backend/schemas/members.py` | **NEW** — Request/response schemas for members, invitations, profile update |
| `src/taskyn/web/backend/routes/members.py` | **NEW** — Company members CRUD + leave + transfer ownership |
| `src/taskyn/web/backend/routes/invitations.py` | **NEW** — Invitations CRUD + accept/decline + my invitations |
| `src/taskyn/web/backend/routes/project_members.py` | **NEW** — Project role override CRUD |
| `src/taskyn/web/backend/routes/auth.py` | Add PATCH /auth/me, extend registration (workspace + invitations), add migration call |
| `src/taskyn/web/backend/routes/companies.py` | Add membership checks, create meta+member on POST, prevent personal workspace delete |
| `src/taskyn/web/backend/routes/projects.py` | Add access checks (viewer/editor/admin per operation), filter lists |
| `src/taskyn/web/backend/routes/nodes.py` | Add project access checks via node's project_id |
| `src/taskyn/web/backend/routes/edges.py` | Add access checks on source/target nodes |
| `src/taskyn/web/backend/routes/milestones.py` | Add project access checks |
| `src/taskyn/web/backend/routes/tags.py` | Add project access checks via node |
| `src/taskyn/web/backend/routes/timer.py` | Add project access checks (editor for mutations) |
| `src/taskyn/web/backend/routes/time_entries.py` | Add project access checks (viewer/editor) |
| `src/taskyn/web/backend/routes/dashboard.py` | Filter by accessible projects |
| `src/taskyn/web/backend/routes/search.py` | Filter results by accessible projects |
| `src/taskyn/web/backend/routes/activity.py` | Filter by accessible entities |
| `src/taskyn/web/backend/main.py` | Register new routers (members, invitations, project_members), add migration to lifespan |
| `src/taskyn/web/backend/deps.py` | Add `ensure_personal_workspace` utility |
| `src/taskyn/web/frontend/src/types/index.ts` | Add CompanyMember, ProjectMember, Invitation, role types |
| `src/taskyn/web/frontend/src/api/client.ts` | Add API methods for new endpoints |

---

## Future Work (Out of Scope)

- **Frontend UI for team management** — pages for team settings, member management, invitation inbox, project sharing UI. Needs separate design.
- **Email delivery for invitations** — currently in-app only. Would need an email service integration.
- **Email verification and password reset** — user account security features.
- **OAuth/SSO providers** — Google, GitHub login.
- **Fine-grained node-level permissions** — currently permissions are project-level. Node-level would add complexity for minimal gain in a PM tool.
- **Audit logging of permission changes** — who changed what role, when.
- **Cross-team project sharing** — sharing a project with users from different teams without adding them to the team.
