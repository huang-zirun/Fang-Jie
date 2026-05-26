# Fix admin data loading log

## 2026-05-26
- Started investigation from `journey/design.md` and current dashboard code.
- Initial suspects:
  - `Admin.vue` calls `/admin/stats`, but the backend route requires `require_admin`; normal anonymous startup tokens are `user` role.
  - The dashboard renders `today_*`, `intent_distribution`, and `problem_stats`, while `/admin/stats` currently returns only global totals/rates.
  - `Admin.vue` source appears mojibake/corrupted in several template and TypeScript string literals, which may also break frontend compilation.
- Frontend build passed, so the visible startup failure is not a compile-time failure.
- Confirmed root cause:
  - The dashboard boot flow obtains an anonymous `user` token, then calls an admin-only endpoint and receives 403.
  - Even with admin credentials, `/admin/stats` did not match the dashboard schema.
- Fix:
  - Added `GET /api/v1/tasks/overview` for authenticated current-user operations overview.
  - Kept `/api/v1/admin/stats` protected by `require_admin`.
  - Updated the dashboard to call `/tasks/overview`.
  - Added regression coverage for the overview contract and admin protection.
- Verification:
  - `uv run pytest tests\test_task_overview.py tests\test_next_task.py tests\test_task_swap.py tests\test_diagnosis.py`
  - `npm run build`
  - Live Vite proxy call to `http://127.0.0.1:5173/api/v1/tasks/overview`
