# Fix admin data loading

## Problem
The operations dashboard reports data loading failures on startup. The fix must identify the real contract or runtime breakage instead of adding a local fallback or fake data.

## Plan
1. Reproduce the failure through frontend build and backend API tests.
2. Trace the dashboard data flow: `Admin.vue` -> `frontend/src/api/tasks.ts` -> FastAPI routes.
3. Fix the root cause at the interface or backend layer so the dashboard receives the data shape it renders.
4. Add focused regression coverage for the affected API behavior.
5. Run backend tests and frontend build to verify.

## Constraints
- No ad hoc patching or client-side masking of server errors.
- Preserve RBAC semantics where admin-only mutation/config routes remain protected.
- Avoid touching unrelated dirty worktree changes.
