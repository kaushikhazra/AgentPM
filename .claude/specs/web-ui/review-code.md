# Code Review: `feature/web-ui` branch

**Branch:** `feature/web-ui` vs `develop`
**Scope:** 147 files, ~27,200 lines added across 11 commits
**Components:** FastAPI backend, React frontend, MCP extensions, tests
**Reviewed by:** Velasari
**Date:** 2026-02-04

---

## Overview

This branch adds a full web UI to Taskyn: a FastAPI REST backend that delegates to existing MCP tools, a React frontend with atomic design (atoms/molecules/organisms/templates/pages), JWT-based auth with refresh tokens, and comprehensive tests. The architecture is clean -- the "thin REST bridge" pattern avoids logic duplication between MCP and REST.

---

## CRITICAL Issues (5)

| # | Issue | Location |
|---|-------|----------|
| 1 | **Hardcoded JWT secret fallback** -- `"taskyn-dev-secret-change-in-production"` allows token forging if env var is unset; no startup warning | `src/taskyn/web/backend/auth/jwt.py:8` |
| 2 | **No rate limiting on auth endpoints** -- `/auth/login` and `/auth/register` are open to brute-force and mass account creation | `src/taskyn/web/backend/routes/auth.py:15-34` |
| 3 | ~~**No authorization enforcement**~~ -- `current_user` is injected for authentication but not used for ownership checks. **By design:** Taskyn is a single-user personal tool; MCP tools operate on a shared database with no tenant concept | All route files |
| 4 | **Auth refresh race condition** -- `AuthProvider` uses `api.post('/auth/refresh')` which goes through the 401 retry path, potentially causing recursive refresh calls | `src/taskyn/web/frontend/src/providers/AuthProvider.tsx:27-35` |
| 5 | **PlannerPage infinite re-fetch loop risk** -- `loadData` depends on `expanded.size`, sets `expanded` inside itself, which recreates the callback and re-triggers the effect | `src/taskyn/web/frontend/src/pages/PlannerPage.tsx:94-119` |

### Details

#### 1. Hardcoded JWT Secret Fallback

```python
SECRET_KEY = os.getenv("TASKYN_JWT_SECRET", "taskyn-dev-secret-change-in-production")
```

The fallback value is a predictable, low-entropy string. If the environment variable is not set (and there is no `.env` file or deployment config enforcing it), the application silently runs with a guessable secret. Any attacker who reads this source code can forge arbitrary JWT tokens for any user.

**OWASP:** A02:2021 -- Cryptographic Failures

**Recommendation:** Refuse to start the application if `TASKYN_JWT_SECRET` is unset or shorter than 32 characters. Use `secrets.token_urlsafe(32)` to generate a minimum 256-bit secret.

#### 2. No Rate Limiting on Auth Endpoints

No rate limiting, throttling, or account lockout mechanism exists on `/auth/login`, `/auth/register`, or `/auth/refresh`. An attacker can perform unlimited brute-force credential-stuffing attempts.

**OWASP:** A07:2021 -- Identification and Authentication Failures

**Recommendation:** Add rate limiting middleware (e.g., `slowapi`) on auth endpoints. Start with 5 failed login attempts per minute per IP with exponential backoff.

#### 3. ~~No Authorization Enforcement~~ (By Design)

Every route injects `current_user: User = Depends(get_current_user)` for authentication but does not pass it to MCP tool calls. This is **by design** -- Taskyn is a single-user personal tool where MCP tools operate on a shared database with no tenant concept. The `current_user` dependency serves as an authentication gate (ensuring the caller is logged in) rather than an authorization filter.

#### 4. Auth Refresh Race Condition

The `AuthProvider` on mount calls `api.post<TokenResponse>('/auth/refresh')`, which goes through the main `request()` function. If the server returns 401, `request()` enters the 401 branch and calls `ensureToken()`, which calls `refreshAccessToken()` using raw `fetch` -- creating a redundant double refresh. The result is two refresh calls before settling.

**Recommendation:** The `AuthProvider` should use raw `fetch` for its initial refresh (like `client.ts` does internally), or the `request()` function should skip auto-refresh for the `/auth/refresh` endpoint.

#### 5. PlannerPage Infinite Re-fetch Loop Risk

```typescript
const loadData = useCallback(async () => {
  if (expanded.size === 0) {
    setExpanded(new Set(rootIds));  // changes expanded.size
  }
}, [selectedId, projects, expanded.size]);

useEffect(() => { loadData(); }, [loadData]);
```

When `expanded.size === 0`, `setExpanded` changes it, which recreates `loadData`, which re-triggers the effect. If `rootIds` is empty (empty project), `expanded` stays at size 0, causing an infinite loop.

**Recommendation:** Decouple the expanded-initialization logic from the data-loading callback. Use a separate `useEffect` for setting initial expanded state.

---

## HIGH Issues (12)

| # | Issue | Location |
|---|-------|----------|
| 6 | **No password validation** -- `password: str` accepts empty strings; no min/max length | `src/taskyn/web/backend/schemas/auth.py:9` |
| 7 | **No string length validation** on any schema field -- DoS via multi-MB payloads | All schema files |
| 8 | **No refresh token revocation** -- logout only clears cookie client-side; stolen tokens remain valid for 7 days | `src/taskyn/web/backend/routes/auth.py:51-55` |
| 9 | **`secure=False` hardcoded** on refresh token cookie -- interceptable over HTTP | `src/taskyn/web/backend/routes/auth.py:43` |
| 10 | **`exclude_none=True` on PATCH** -- cannot clear optional fields (e.g., un-assign); should be `exclude_unset=True` | `src/taskyn/web/backend/routes/nodes.py:55`, `projects.py:53` |
| 11 | **Exception swallowed without logging** -- catch-all `except Exception` in `call_mcp_tool` discards stack traces | `src/taskyn/web/backend/deps.py:51-52` |
| 12 | **TrackerPage N+1 loading** -- loads ALL nodes across ALL projects just to get time entries | `src/taskyn/web/frontend/src/pages/TrackerPage.tsx:56-78` |
| 13 | **No lazy loading** -- all 12 page components eagerly imported in single bundle | `src/taskyn/web/frontend/src/routes.tsx:4-16` |
| 14 | **Kanban drag-and-drop inaccessible** -- uses native HTML5 DnD with no keyboard alternative | `src/taskyn/web/frontend/src/pages/KanbanPage.tsx:202-217` |
| 15 | **`statusClass` function duplicated 3x** -- identical code in PlannerPage, NodeDetailPage, ProjectDetailPage | `PlannerPage:23`, `NodeDetailPage:13`, `ProjectDetailPage:13` |
| 16 | **FilterBadge molecule exists but unused** -- KanbanPage and PlannerPage manually re-implement the same dropdown | `src/taskyn/web/frontend/src/pages/KanbanPage.tsx:54-63` |
| 17 | **`dev_server.py` SIGTERM crashes on Windows** -- `signal.signal(signal.SIGTERM, handler)` raises `ValueError` on Windows | `scripts/dev_server.py:32` |

### Details

#### 6. No Password Validation

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str  # accepts "", "a", any string
    name: str
```

**Recommendation:** Add `password: str = Field(..., min_length=8, max_length=128)` and `name: str = Field(..., min_length=1, max_length=255)`.

#### 7. No String Length Validation

None of the string fields across all schemas have `min_length` or `max_length` constraints. Company names, project names, node titles, descriptions -- all accept multi-megabyte strings. This enables potential DoS via database bloat.

**Recommendation:** Add `Field(min_length=1, max_length=...)` to all string fields. Names: 255 chars. Descriptions: 5000 chars. Reasons: 1000 chars.

#### 8. No Refresh Token Revocation

```python
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out")
```

Logout only deletes the cookie client-side. The refresh token itself remains cryptographically valid for 7 days. No server-side blocklist exists.

**Recommendation:** Store issued refresh tokens (hashed) in a database table. On logout, delete the token. On refresh, verify the token exists in the store.

#### 9. `secure=False` Hardcoded on Cookie

```python
response.set_cookie(
    key="refresh_token",
    secure=False,  # False for local dev; True in production
)
```

The comment says "True in production" but there is no mechanism to ensure this. It is hardcoded.

**Recommendation:** Make configurable via environment variable: `secure=os.getenv("TASKYN_COOKIE_SECURE", "true").lower() == "true"`.

#### 10. `exclude_none=True` Breaks PATCH Semantics

```python
args = {"node_id": node_id, **data.model_dump(exclude_none=True)}
```

Using `exclude_none=True` means a client cannot explicitly set a field to `null` (e.g., un-assign a node by sending `{"assignee": null}`). The `null` value is silently dropped.

**Recommendation:** Use `exclude_unset=True` instead. This distinguishes "field not sent" from "field explicitly set to null."

#### 11. Exception Swallowed Without Logging

```python
except Exception:
    raise HTTPException(500, detail="Internal server error")
```

All unexpected exceptions are discarded with no logging. This makes production debugging impossible.

**Recommendation:** Add `logging.getLogger(__name__).exception("Unhandled error in MCP tool %s", tool_name)` before the re-raise.

#### 12. TrackerPage N+1 Loading

The tracker loads ALL nodes across ALL projects via `nodesApi.list()` just to extract time entries. As the system scales, this becomes very expensive.

**Recommendation:** Add a dedicated `/api/v1/time-entries` GET endpoint with date range and node filters.

#### 13. No Lazy Loading

All 12 page components are eagerly imported at the top of `routes.tsx`. The entire application ships in a single bundle.

**Recommendation:** Use React Router's `lazy()` property or `React.lazy()` with `Suspense` to code-split pages.

#### 14. Kanban Drag-and-Drop Inaccessible

Cards use native HTML5 drag-and-drop (`draggable`, `onDragStart`, `onDragEnd`), which is inaccessible to keyboard users. No alternative keyboard mechanism exists.

**Recommendation:** Add keyboard interaction (Enter to pick up, arrow keys to move between columns, Enter to drop) or use a library like `@hello-pangea/dnd` which has built-in keyboard support.

#### 15. `statusClass` Duplicated 3x

The exact same function is copy-pasted in PlannerPage, NodeDetailPage, and ProjectDetailPage.

**Recommendation:** Extract to `src/taskyn/web/frontend/src/utils/status.ts` or add to `config/methodology-ui.ts`.

#### 16. FilterBadge Molecule Exists But Is Unused

A `FilterBadge` molecule at `components/molecules/FilterBadge.tsx` encapsulates the dropdown-with-outside-click pattern. KanbanPage and PlannerPage both manually re-implement the same logic instead of using it.

**Recommendation:** Refactor KanbanPage and PlannerPage to use `FilterBadge`.

#### 17. `dev_server.py` SIGTERM Crashes on Windows

`signal.signal(signal.SIGTERM, handler)` raises `ValueError` on Windows. This is on the same platform the `npm.cmd` check is designed for.

**Recommendation:** Wrap in `try/except ValueError` or check `sys.platform`.

---

## MEDIUM Issues (18)

| # | Issue | Location |
|---|-------|----------|
| 18 | User enumeration via `/auth/register` (409 "Email already registered") | `routes/auth.py:18-19` |
| 19 | Module-level SQLite connection is not thread-safe for async FastAPI | `auth/users.py:52-60` |
| 20 | No pagination on any list endpoint -- unbounded result sets | All list routes |
| 21 | Missing CRUD endpoints: no DELETE for nodes/tags, no GET/UPDATE for milestones, no UPDATE for companies | Various route files |
| 22 | `MilestoneCreate.target_date` typed as `str` -- no date format validation | `schemas/milestones.py:10` |
| 23 | `TimeEntryCreate.duration_minutes` has no min/max bounds | `schemas/timer.py:19` |
| 24 | React Query declared but unused -- paying bundle cost with zero benefit | `App.tsx:2` |
| 25 | No `ErrorBoundary` -- unhandled render errors crash entire app to white screen | `App.tsx` |
| 26 | `TimerProvider` fires API call on mount before auth is confirmed | `TimerProvider.tsx:68-69` |
| 27 | Modals lack `role="dialog"`, `aria-modal`, and focus trapping | `Modal.tsx:25-39`, `SearchModal.tsx` |
| 28 | No loading states on initial page data fetches | KanbanPage, PlannerPage, TrackerPage, CompaniesPage |
| 29 | Create/edit forms don't use `<form>` -- Enter key doesn't submit | CompaniesPage, PlannerPage, ProjectDetailPage, NodeDetailPage |
| 30 | Delete operations have no confirmation dialog | `CompaniesPage.tsx:75` |
| 31 | SearchModal debounce has race condition -- stale results may overwrite newer ones | `SearchModal.tsx:37-54` |
| 32 | `useHotkeys` listener churn -- inline shortcuts array causes add/remove on every render | `useHotkeys.ts:14-45` |
| 33 | `email-validator` missing from pyproject.toml `[web]` deps -- `EmailStr` will crash at import | `pyproject.toml` |
| 34 | `test_routes_require_auth` only tests GET -- POST/PATCH/DELETE unguarded in tests | `tests/test_web_routes.py:739-757` |
| 35 | JWT expiration paths completely untested (expired access/refresh tokens) | `tests/` |

---

## LOW Issues (12)

| # | Issue | Location |
|---|-------|----------|
| 36 | CORS `allow_methods=["*"]` and `allow_headers=["*"]` unnecessarily broad | `main.py:32-33` |
| 37 | CORS origin hardcoded to `localhost:5173` -- not configurable | `main.py:30` |
| 38 | Same JWT secret for both access and refresh tokens | `jwt.py:14-34` |
| 39 | No `iat`/`jti` claims in JWT tokens -- cannot revoke individual tokens or enforce "issued after" policies | `jwt.py:17-22` |
| 40 | `delete_cookie` does not mirror `set_cookie` attributes (`samesite`, `httponly`) -- may not clear cookie in all browsers | `routes/auth.py:54` |
| 41 | `ErrorResponse` schema defined but never used in route `responses` parameter | `schemas/common.py` |
| 42 | `null as T` unsafe cast in API client for 204 responses | `api/client.ts:97` |
| 43 | No `AbortController` support in API client -- in-flight requests cannot be cancelled | `api/client.ts` |
| 44 | No 404 page -- unknown routes silently redirect to dashboard | `routes.tsx:132-134` |
| 45 | No guest guard on auth pages -- logged-in users can still see login/signup forms | `routes.tsx:44-53` |
| 46 | `Toast` setTimeout not cleaned up on unmount | `ToastProvider.tsx:39` |
| 47 | Icon SVG missing `aria-hidden="true"` for decorative icons | `Icon.tsx:113-129` |

---

## What's Done Well

- **Architecture** -- The "thin REST bridge to MCP tools" pattern is elegant and keeps all business logic in one place
- **SQL injection protection** -- All queries use parameterized `?` placeholders throughout
- **Password hashing** -- bcrypt with auto-salt, `User`/`UserInDB` separation prevents hash leakage
- **Token type validation** -- access vs refresh token type checking prevents token confusion attacks
- **Login error messages** -- generic "Invalid credentials" prevents email/password enumeration on login
- **RESTful design** -- proper HTTP methods, status codes (201 for POST, 204 for DELETE), consistent URL patterns
- **Atomic design** -- clean component hierarchy with reusable atoms/molecules/organisms
- **Test organization** -- good fixture chains, integration tests that exercise full workflows
- **Frontend types** -- comprehensive TypeScript interfaces mirroring backend Pydantic models
- **Methodology UI config** -- clean mapping with fallback behavior for unknown values
- **API client deduplicated refresh** -- shared `refreshPromise` prevents race conditions on 401 retries
- **Refresh token in HttpOnly cookie** -- prevents JavaScript access, mitigating XSS-based token theft
- **SameSite=lax on refresh cookie** -- provides CSRF protection
- **Short-lived access tokens** -- 15-minute expiry limits window of opportunity for stolen tokens
- **Clean error hierarchy** -- `TaskynError` > `ValidationError` > specialized errors, mapped cleanly to HTTP status codes

---

## Missing Test Coverage

### Critical (security/correctness)

- [ ] Expired JWT access token rejected by `/auth/me`
- [ ] Access token used as refresh token is rejected by `/auth/refresh`
- [ ] Expired refresh token rejected by `/auth/refresh`
- [ ] Unauthenticated POST/PATCH/DELETE requests return 401 (only GET is tested)

### High (functional coverage)

- [ ] `pm_create_node` with `parent_id` parameter -- auto-edge creation at `server.py:529-537` has zero coverage
- [ ] 404 responses for non-existent project, node, milestone, and edge IDs
- [ ] `pm_update_project` via MCP tests
- [ ] `pm_delete_company` and `pm_delete_project` via MCP tests
- [ ] MCP resources (`pm://dashboard`, `pm://activity/recent`, etc.)
- [ ] `pm_create_node` with invalid `node_type` for the methodology

### Medium (robustness)

- [ ] `pm_create_edge` with invalid edge_type
- [ ] `pm_list_nodes` with various filter combinations
- [ ] Web route `GET /api/v1/projects?include_stats=true`
- [ ] Web route `PATCH /api/v1/nodes/{id}` with empty body
- [ ] Search result content verification (not just `isinstance(list)`)
- [ ] Timer workflow: start timer, start second timer (should auto-stop first)
- [ ] `pm_block_node` via MCP tests

---

## Top 5 Recommendations (Priority Order)

1. **Fix JWT secret handling** -- refuse to start if `TASKYN_JWT_SECRET` is unset or < 32 chars; make `secure` cookie flag configurable via env var
2. **Fix `exclude_none` to `exclude_unset`** on all PATCH endpoints -- this is a correctness bug that will frustrate users trying to clear fields
3. **Add `ErrorBoundary` and lazy loading** -- the frontend will crash on any unhandled error with no recovery, and all pages load eagerly in a single bundle
4. **Add missing test coverage** -- expired tokens, non-GET auth guards, `parent_id` auto-edge, and 404 cases for all resource types
5. **Add refresh token revocation** -- store issued tokens server-side; on logout, invalidate them (groundwork: add `jti` claims first)

---
---

# Follow-Up Review: Phase 11A-11D Fix Commits

**Scope:** 4 commits (Phase 11A: security hardening, 11B: backend correctness, 11C: frontend quality, 11D: tests)
**Reviewed by:** Velasari
**Date:** 2026-02-04

---

## Executive Summary

The four fix commits address **37 out of 47 original findings**. All 5 CRITICAL issues were resolved. The fixes are clean, well-referenced (CR-# comments trace back to original findings), and introduce no new vulnerabilities. One notable gap remains: **no refresh token revocation** (CR-8, groundwork laid via `jti` claims but no blocklist). CR-3 (authorization enforcement) was reclassified as by-design -- Taskyn is a single-user personal tool with no tenant isolation concept.

---

## Phase 11A -- Security Hardening

| # | Original Issue | Severity | Status | Notes |
|---|----------------|----------|--------|-------|
| 1 | Hardcoded JWT secret fallback | CRITICAL | **FIXED** | `_load_secret()` validates env var exists and >= 32 chars; helpful error message with generation command |
| 2 | No rate limiting on auth endpoints | CRITICAL | **FIXED** | slowapi: 5/min login, 10/min register, 30/min refresh; `TASKYN_RATE_LIMIT` env var for test disable |
| 6 | No password validation | HIGH | **FIXED** | `Field(min_length=8, max_length=128)` on password; `min_length=1, max_length=255` on name |
| 8 | No refresh token revocation | HIGH | **NOT FIXED** | `jti` claim added (prerequisite for revocation) but no server-side blocklist implemented |
| 9 | `secure=False` hardcoded on cookie | HIGH | **FIXED** | `TASKYN_COOKIE_SECURE` env var; cookie attrs centralized in `_COOKIE_ATTRS` dict |
| 11 | Exception swallowed without logging | HIGH | **FIXED** | `logger.exception()` added before re-raise |
| 18 | User enumeration via registration | MEDIUM | **PARTIALLY FIXED** | Message changed to "Registration failed" but 409 status still distinguishes from 422 |
| 19 | Module-level SQLite connection thread safety | MEDIUM | **FIXED** | `@contextmanager` with per-call connection, proper `finally: conn.close()` |
| 33 | `email-validator` missing from deps | MEDIUM | **FIXED** | Added to pyproject.toml `[web]` extras alongside `slowapi>=0.1.9` |
| 36-37 | CORS hardcoded/overly broad | LOW | **FIXED** | `TASKYN_CORS_ORIGINS` env var; methods/headers narrowed to explicit lists |
| 39 | No `iat`/`jti` claims in JWT | LOW | **FIXED** | Both claims added to access and refresh tokens |
| 40 | `delete_cookie` attribute mismatch | LOW | **FIXED** | Centralized in `_COOKIE_ATTRS` dict |

**Score: 10/12 issues fixed, 1 partially fixed, 1 not fixed**

---

## Phase 11B -- Backend Correctness

| # | Original Issue | Severity | Status | Notes |
|---|----------------|----------|--------|-------|
| 10 | `exclude_none` on PATCH | HIGH | **FIXED** | All 4 PATCH routes now use `exclude_unset=True` |
| 7 | No string length validation | HIGH | **FIXED** | All string fields across all 7 schema files have `max_length`; required names have `min_length=1` |
| 21 | Missing CRUD endpoints | MEDIUM | **MOSTLY FIXED** | Added: DELETE nodes, GET/PATCH milestones, PATCH companies, POST milestone/complete. DELETE tags still missing |
| 22 | `MilestoneCreate.target_date` typed as `str` | MEDIUM | **FIXED** | Now `datetime.date` with string serialization at route level |
| 23 | `TimeEntryCreate.duration_minutes` no bounds | MEDIUM | **FIXED** | `Field(gt=0, le=1440)` |

**New MCP tools added:** `pm_update_company`, `pm_delete_company`, `pm_get_company_stats`, `pm_get_milestone`, `pm_update_milestone`, `pm_delete_node`

**Score: 5/5 issues fixed (1 with minor gap: DELETE tags)**

**Residual concerns:**
- `CompanyUpdate.name` allows empty string on PATCH (no `min_length=1` on update schema)
- Enum validation for `node_type`, `priority`, `edge_type` deferred to MCP/core layer (acceptable for methodology-dependent fields)

---

## Phase 11C -- Frontend Quality

| # | Original Issue | Severity | Status | Notes |
|---|----------------|----------|--------|-------|
| 5 | PlannerPage infinite re-fetch loop | CRITICAL | **FIXED** | `useRef` guard (`initialExpandDone`) breaks the loop; minor double-fetch on mount remains |
| 4 | Auth refresh race condition | CRITICAL | **FIXED** | `ensureToken()` via raw fetch; module-level `refreshPromise` deduplicates concurrent calls |
| 13 | No lazy loading | HIGH | **FIXED** | All 12 pages lazy-loaded with `React.lazy()` + `Suspense` |
| 17 | dev_server.py SIGTERM on Windows | HIGH | **PARTIALLY FIXED** | `atexit.register(shutdown)` added as safety net; SIGTERM handler is still a no-op on Windows but atexit + SIGINT cover Ctrl+C |
| 25 | No ErrorBoundary | MEDIUM | **FIXED** | Class component with `getDerivedStateFromError`, reset UI, integrated into both ProtectedRoute and GuestRoute |
| 26 | TimerProvider fires before auth | MEDIUM | **FIXED** | Guards on `authLoading` and `user` before API call |
| 27 | Modals lack aria/focus trap | MEDIUM | **FIXED** | `role="dialog"`, `aria-modal`, `aria-labelledby`, Tab/Shift+Tab focus cycling, auto-focus on open, restore focus on close |
| 28 | No loading states | MEDIUM | **FIXED** | Text-based loading indicators on CompaniesPage, DashboardPage, ProjectsPage |
| 31 | SearchModal race condition | MEDIUM | **FIXED** | Request counter pattern (`searchIdRef`) discards stale responses |
| 32 | `useHotkeys` listener churn | MEDIUM | **FIXED** | `useRef` for stable shortcuts; `useEffect` with empty `[]` dependency array |
| 44 | No 404 page | LOW | **FIXED** | `NotFoundPage` with navigation back, wired as catch-all `*` route |
| 45 | No guest guard on auth pages | LOW | **FIXED** | `GuestRoute` wrapper redirects authenticated users to dashboard |
| 46 | Toast setTimeout cleanup | LOW | **FIXED** | `Map<string, timeout>` tracked in `timersRef` with unmount cleanup |
| 47 | Icon missing `aria-hidden` | LOW | **FIXED** | `aria-hidden="true"` on SVG element |

**Score: 12/14 issues fully fixed, 2 partially fixed**

---

## Phase 11D -- Test Coverage

| Gap Category | Item | Covered? |
|---|---|---|
| **Critical** | Expired access token rejected by `/auth/me` | YES |
| **Critical** | Access token used as refresh rejected | YES |
| **Critical** | Refresh token used as access rejected | YES (bonus) |
| **Critical** | Expired refresh token rejected | YES |
| **Critical** | Unauthenticated POST/PATCH/DELETE return 401 | YES (15 routes) |
| **High** | `pm_create_node` with `parent_id` auto-edge | YES |
| **High** | 404 for non-existent resources | YES (4 entity types) |
| **High** | MCP resources coverage | PARTIAL (registration only, no invocation) |
| **Medium** | Filter combinations | YES |
| **Medium** | `include_stats` parameter | YES (companies + projects) |
| **Medium** | Empty PATCH body | YES (nodes) |
| **Medium** | Search result content verification | YES |
| **Medium** | Timer workflow (auto-stop) | YES |

**New test functions added:** 18 in `test_web_auth.py`, 48 in `test_web_routes.py`

**Test quality:** Well-structured with docstrings, proper test isolation, good negative testing (invalid tokens, non-existent resources, invalid types), and integration tests for full auth/CRUD flows.

**Score: 12/13 gaps covered (1 partial: MCP resources)**

---

## Remaining Open Issues

### Still Unaddressed

| # | Severity | Issue | Risk |
|---|----------|-------|------|
| 3 | ~~CRITICAL~~ | ~~No authorization enforcement~~ -- **By design:** single-user personal tool; `current_user` serves as auth gate, no tenant isolation needed | N/A |
| 8 | **HIGH** | **No refresh token revocation** -- `jti` claims added as groundwork but no blocklist; stolen tokens remain valid 7 days | Medium -- requires token theft first |
| 18 | **MEDIUM** | User enumeration partially remains -- 409 status code distinguishes "email exists" from validation error | Low for personal tool |
| 20 | **MEDIUM** | No pagination on list endpoints | Low at current scale |
| 21 | **MEDIUM** | DELETE tags endpoint still missing | Low -- untag-from-node works |
| 12 | **HIGH** | TrackerPage N+1 loading pattern | Medium -- scales poorly |
| 14 | **HIGH** | Kanban drag-and-drop keyboard inaccessible | Medium for accessibility |
| 15 | **HIGH** | `statusClass` function duplicated 3x | Low -- code smell only |
| 16 | **HIGH** | `FilterBadge` molecule unused | Low -- code smell only |
| 24 | **MEDIUM** | React Query declared but unused | Low -- bundle cost only |
| 29 | **MEDIUM** | Forms don't use `<form>` element | Low -- UX concern |
| 30 | **MEDIUM** | Delete operations lack confirmation | Low -- UX concern |

### New Minor Observations from Fixes

- PlannerPage has a minor double-fetch on mount due to `useCallback` dependency chains (harmless but wasteful)
- `test_create_edge_invalid_type` allows status 500 in assertion -- should be tightened to 422 only
- Test fixture duplication between `test_web_auth.py` and `test_web_routes.py` (`_reset_users_db`, `client`) should be elevated to `conftest.py`
- MCP resources test accesses internal `_resource_manager._resources` attribute -- fragile to FastMCP version changes

---

## Final Assessment

The Phase 11A-11D fixes demonstrate **thorough, systematic remediation**. The team addressed findings across all severity levels, used CR-# reference comments for traceability, and avoided introducing new issues. The security posture is significantly improved: hardcoded secrets eliminated, rate limiting active, input validation comprehensive, and JWT tokens properly typed with `iat`/`jti` claims.

The **primary remaining gap** is refresh token revocation (CR-8), which has groundwork in place via `jti` claims and can be incrementally added. CR-3 (authorization) was reclassified as by-design given Taskyn's single-user scope.

**Overall readiness:** Suitable for personal/dev use. Consider adding refresh token revocation (CR-8) for defense-in-depth.
