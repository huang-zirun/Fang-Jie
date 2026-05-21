import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.optimization_rule import OptimizationRule
from app.models.performance_report import PerformanceReport
from app.models.platform import Platform
from app.models.intent import Intent
from app.schemas.report import ReportCreate, ReportResponse, DiagnosisOut as DiagnosisResultOut
from app.schemas.task import TaskCreate, TaskOut, TaskHistoryOut
from app.services.diagnosis_service import diagnose_performance
from app.services.task_service import generate_task, get_current_task
from app.services.conversion_service import get_conversion_scripts

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _build_task_out(db: AsyncSession, task) -> TaskOut:
    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == task.platform_id)
    )
    platform_row = platform_result.first()

    intent_result = await db.execute(
        Intent.__table__.select().where(Intent.id == task.intent_id)
    )
    intent_row = intent_result.first()
    intent_name = intent_row.name if intent_row else None

    conversion_scripts = None
    if task.intent_id:
        conversion_scripts = await get_conversion_scripts(db, task.intent_id)

    return TaskOut(
        id=task.id,
        platform_name=platform_row.name if platform_row else "",
        hook_text=task.hook_text,
        storyboard=task.storyboard,
        script_text=task.script_text,
        title=task.title,
        comment_template=task.comment_template,
        why_it_works=task.why_it_works,
        is_optimized=task.is_optimized,
        optimization_note=task.optimization_note,
        prev_task_id=task.prev_task_id,
        created_at=task.created_at,
        intent_name=intent_name,
        conversion_scripts=conversion_scripts,
    )


@router.post("/cleanup/expired")
async def cleanup_expired_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.task_cleanup import expire_old_tasks
    count = await expire_old_tasks()
    return {"expired_count": count}


@router.get("/history", response_model=list[TaskHistoryOut])
async def get_task_history(
    intent_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(ContentTask)
        .where(ContentTask.user_id == current_user.id)
        .order_by(ContentTask.created_at.desc())
    )
    if intent_id:
        query = query.where(ContentTask.intent_id == intent_id)
    if status:
        query = query.where(ContentTask.status == status)

    result = await db.execute(query)
    tasks = result.scalars().all()

    history_list: list[TaskHistoryOut] = []
    for task in tasks:
        intent_result = await db.execute(
            Intent.__table__.select().where(Intent.id == task.intent_id)
        )
        intent_row = intent_result.first()
        intent_name = intent_row.name if intent_row else ""

        platform_result = await db.execute(
            Platform.__table__.select().where(Platform.id == task.platform_id)
        )
        platform_row = platform_result.first()
        platform_name = platform_row.name if platform_row else ""

        problem_type = None
        problem_desc = None
        if task.diagnosis_id:
            diag_result = await db.execute(
                DiagnosisResult.__table__.select().where(DiagnosisResult.id == task.diagnosis_id)
            )
            diag_row = diag_result.first()
            if diag_row:
                problem_type = diag_row.problem_type
                problem_desc = diag_row.problem_desc

        play_count = None
        comment_count = None
        message_count = None
        if task.report:
            play_count = task.report.play_count
            comment_count = task.report.comment_count
            message_count = task.report.message_count

        history_list.append(TaskHistoryOut(
            id=task.id,
            intent_name=intent_name,
            platform_name=platform_name,
            status=task.status,
            task_type=task.task_type,
            hook_text=task.hook_text,
            title=task.title,
            created_at=task.created_at,
            published_at=task.published_at,
            problem_type=problem_type,
            problem_desc=problem_desc,
            play_count=play_count,
            comment_count=comment_count,
            message_count=message_count,
        ))

    return history_list


@router.post("", response_model=TaskOut)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        task = await generate_task(
            db=db,
            user_id=current_user.id,
            intent_id=data.intent_id,
            platform_id=data.platform_id,
            task_type=data.task_type,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "HAS_PENDING_TASK":
            existing = await get_current_task(db, current_user.id)
            if existing:
                return await _build_task_out(db, existing)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Has pending task")
        elif "Intent" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "Platform" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == task.platform_id)
    )
    platform_row = platform_result.first()

    return await _build_task_out(db, task)


@router.get("/current", response_model=TaskOut)
async def get_current_task_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await get_current_task(db, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current task")

    return await _build_task_out(db, task)


@router.post("/{task_id}/publish")
async def publish_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        ContentTask.__table__.select().where(ContentTask.id == task_id)
    )
    task_row = result.first()
    if not task_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task_row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")
    if task_row.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task status incorrect")

    await db.execute(
        update(ContentTask)
        .where(ContentTask.id == task_id)
        .values(status="PUBLISHED", published_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return {"message": "正在追踪你的内容表现", "task_id": str(task_id), "status": "PUBLISHED"}


@router.post("/{task_id}/swap", response_model=TaskOut)
async def swap_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentTask).where(ContentTask.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    swap_count_today = 0
    if task.created_at and task.created_at >= today_start:
        swap_count_today = task.swap_count

    if swap_count_today >= 1:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日换条次数已用",
        )

    await db.delete(task)

    try:
        new_task = await generate_task(
            db=db,
            user_id=current_user.id,
            intent_id=task.intent_id,
            platform_id=task.platform_id,
            task_type=task.task_type,
        )
        new_task.swap_count = swap_count_today + 1
        await db.commit()
        await db.refresh(new_task)
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "HAS_PENDING_TASK":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Has pending task")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return await _build_task_out(db, new_task)


@router.post("/{task_id}/report", response_model=ReportResponse)
async def report_task(
    task_id: uuid.UUID,
    data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentTask).where(ContentTask.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")
    if task.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be published first")

    existing_report = await db.execute(
        select(PerformanceReport).where(PerformanceReport.task_id == task_id)
    )
    if existing_report.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task already reported")

    report = PerformanceReport(
        task_id=task_id,
        play_count=data.play_count,
        comment_count=data.comment_count,
        message_count=data.message_count,
    )
    db.add(report)

    await db.execute(
        update(ContentTask).where(ContentTask.id == task_id).values(status="REPORTED")
    )
    await db.commit()
    await db.refresh(report)

    diagnosis = await diagnose_performance(db, report)

    if diagnosis.problem_type != "normal":
        matched_rule_result = await db.execute(
            select(OptimizationRule).where(
                OptimizationRule.problem_type == diagnosis.problem_type,
                OptimizationRule.is_active.is_(True),
            )
        )
        matched_rule = matched_rule_result.scalars().first()
        if matched_rule:
            matched_rule.hit_count += 1

    if task.prev_task_id:
        prev_diag_result = await db.execute(
            select(DiagnosisResult).join(
                ContentTask, ContentTask.diagnosis_id == DiagnosisResult.id
            ).where(ContentTask.id == task.prev_task_id)
        )
        prev_diagnosis = prev_diag_result.scalars().first()
        if prev_diagnosis and prev_diagnosis.problem_type != "normal":
            prev_report_result = await db.execute(
                select(PerformanceReport).where(PerformanceReport.task_id == task.prev_task_id)
            )
            prev_report = prev_report_result.scalars().first()
            if prev_report and report.play_count > prev_report.play_count:
                prev_rule_result = await db.execute(
                    select(OptimizationRule).where(
                        OptimizationRule.problem_type == prev_diagnosis.problem_type,
                        OptimizationRule.is_active.is_(True),
                    )
                )
                prev_rule = prev_rule_result.scalars().first()
                if prev_rule:
                    prev_rule.accuracy_count += 1

    await db.execute(
        update(ContentTask).where(ContentTask.id == task_id).values(
            status="DIAGNOSED",
            diagnosis_id=diagnosis.id,
        )
    )
    await db.commit()

    return ReportResponse(
        diagnosis=DiagnosisResultOut(
            problem_type=diagnosis.problem_type,
            problem_desc=diagnosis.problem_desc,
            optimization_direction=diagnosis.optimization_direction,
            optimization_detail=diagnosis.optimization_detail,
            ai_analysis=diagnosis.ai_analysis,
            rule_confidence=diagnosis.rule_confidence,
        )
    )


@router.get("/{task_id}/diagnosis", response_model=DiagnosisResultOut)
async def get_diagnosis(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentTask).where(ContentTask.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")
    if task.status != "DIAGNOSED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not available")

    diag_result = await db.execute(
        select(DiagnosisResult).where(DiagnosisResult.task_id == task_id)
    )
    diagnosis = diag_result.scalars().first()
    if not diagnosis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")

    return DiagnosisResultOut(
        problem_type=diagnosis.problem_type,
        problem_desc=diagnosis.problem_desc,
        optimization_direction=diagnosis.optimization_direction,
        optimization_detail=diagnosis.optimization_detail,
        ai_analysis=diagnosis.ai_analysis,
        rule_confidence=diagnosis.rule_confidence,
    )


@router.post("/{task_id}/next", response_model=TaskOut)
async def get_next_task(
    task_id: uuid.UUID,
    platform_id: uuid.UUID = Query(...),
    task_type: str = Query("video"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentTask).where(ContentTask.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")
    if task.status != "DIAGNOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please complete data report first")

    diag_result = await db.execute(
        select(DiagnosisResult).where(DiagnosisResult.task_id == task_id)
    )
    diagnosis = diag_result.scalars().first()

    optimization_prompt = None
    if diagnosis:
        optimization_prompt = diagnosis.optimization_detail

    try:
        new_task = await generate_task(
            db=db,
            user_id=current_user.id,
            intent_id=task.intent_id,
            platform_id=platform_id,
            task_type=task_type,
            optimization_prompt=optimization_prompt,
            prev_task_id=task_id,
            diagnosis_id=diagnosis.id if diagnosis else None,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "HAS_PENDING_TASK":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Has pending task")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return await _build_task_out(db, new_task)
