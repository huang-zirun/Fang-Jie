# Fix next optimized task

- Started root-cause analysis for data report next-task button.
- Initial finding: frontend sends JSON body to /tasks/{id}/next, backend expects required query parameter platform_id, causing 422 instead of task generation.
- Secondary finding: frontend hardcodes Douyin platform id because TaskOut does not include platform_id.
- Fixed backend contract with TaskNextCreate: body accepts optional platform_id and task_type; omitted values default to the diagnosed task's own platform/type.
- Added intent_id, platform_id, and task_type to TaskOut.
- Updated DataReport.vue to load the route task, reload diagnosis for diagnosed tasks, and stop hardcoding Douyin.
- Added tests/test_next_task.py covering JSON body /next calls and same-platform fallback.
- Verification passed: uv run pytest tests/test_next_task.py tests/test_task_swap.py; npm run build.
