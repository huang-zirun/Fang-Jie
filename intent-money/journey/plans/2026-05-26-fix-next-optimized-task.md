# Fix next optimized task

## Problem
On the data report page, clicking "get next optimized task" appears to do nothing after diagnosis.

## Root cause
The frontend sent a JSON body to `POST /tasks/{id}/next`, while the backend required `platform_id` as a query parameter. FastAPI returned 422, so no optimized task was created. The frontend also hardcoded the Douyin platform id because `TaskOut` did not expose `platform_id`.

## Completed plan
1. Verified the click path from `DataReport.vue` through `frontend/src/api/tasks.ts` to `backend/app/api/v1/tasks.py`.
2. Changed the backend contract to accept a typed JSON body for next-task generation.
3. Defaulted omitted `platform_id` and `task_type` to the diagnosed task's existing platform/type.
4. Exposed `intent_id`, `platform_id`, and `task_type` in `TaskOut`.
5. Updated the data report page to load the route task, reload diagnosis when needed, and stop hardcoding platform ids.
6. Added a regression test for JSON-body next-task creation and same-platform fallback.

## Verification
- `uv run pytest tests/test_next_task.py tests/test_task_swap.py`
- `npm run build`
