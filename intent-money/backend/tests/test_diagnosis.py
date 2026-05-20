import pytest

from app.services.diagnosis_service import _evaluate_condition


@pytest.mark.asyncio
async def test_evaluate_simple_lt():
    condition = {"field": "play_count", "operator": "lt", "value": 500}
    assert _evaluate_condition(condition, 100, 5, 0) is True
    assert _evaluate_condition(condition, 600, 5, 0) is False


@pytest.mark.asyncio
async def test_evaluate_simple_gte():
    condition = {"field": "play_count", "operator": "gte", "value": 500}
    assert _evaluate_condition(condition, 500, 5, 0) is True
    assert _evaluate_condition(condition, 499, 5, 0) is False


@pytest.mark.asyncio
async def test_evaluate_simple_eq():
    condition = {"field": "message_count", "operator": "eq", "value": 0}
    assert _evaluate_condition(condition, 500, 5, 0) is True
    assert _evaluate_condition(condition, 500, 5, 1) is False


@pytest.mark.asyncio
async def test_evaluate_and_condition():
    condition = {
        "and": [
            {"field": "play_count", "operator": "gte", "value": 500},
            {"field": "comment_count", "operator": "lt", "value": 5},
        ]
    }
    assert _evaluate_condition(condition, 600, 3, 0) is True
    assert _evaluate_condition(condition, 400, 3, 0) is False
    assert _evaluate_condition(condition, 600, 6, 0) is False


@pytest.mark.asyncio
async def test_diagnosis_hook_weak():
    from app.services.diagnosis_service import _generate_problem_desc
    from app.models.performance_report import PerformanceReport

    report = PerformanceReport(
        task_id="00000000-0000-0000-0000-000000000099",
        play_count=100,
        comment_count=0,
        message_count=0,
    )
    desc = _generate_problem_desc("hook_weak", report)
    assert "100" in desc
    assert "钩子" in desc


@pytest.mark.asyncio
async def test_diagnosis_normal():
    from app.services.diagnosis_service import _generate_problem_desc
    from app.models.performance_report import PerformanceReport

    report = PerformanceReport(
        task_id="00000000-0000-0000-0000-000000000099",
        play_count=1000,
        comment_count=10,
        message_count=3,
    )
    desc = _generate_problem_desc("normal", report)
    assert "正常" in desc
