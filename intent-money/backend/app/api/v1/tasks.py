import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.optimization_rule import OptimizationRule
from app.models.performance_report import PerformanceReport
from app.models.platform import Platform
from app.models.intent import Intent
from app.schemas.report import ReportCreate, ReportResponse, DiagnosisOut as DiagnosisResultOut
from app.schemas.task import TaskCreate, TaskNextCreate, TaskOut, TaskHistoryOut, TaskOverviewOut
from app.schemas.performance_snapshot import DeployDateUpdate
from app.services.diagnosis_service import diagnose_performance
from app.services.task_service import generate_task, get_current_task
from app.services.conversion_service import get_conversion_scripts
from app.utils.time import utc_day_start_naive, utc_now_naive

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

    latest_snapshot = None
    snapshot_count = 0
    if task.snapshots:
        snapshot_count = len(task.snapshots)
        latest = task.snapshots[-1]
        latest_snapshot = {
            "play_count": latest.play_count,
            "comment_count": latest.comment_count,
            "message_count": latest.message_count,
            "snapshot_at": latest.snapshot_at.isoformat() if latest.snapshot_at else None,
        }

    return TaskOut(
        id=task.id,
        intent_id=task.intent_id,
        platform_id=task.platform_id,
        platform_name=platform_row.name if platform_row else "",
        status=task.status,
        task_type=task.task_type,
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
        published_at=task.published_at,
        deployed_at=task.deployed_at,
        intent_name=intent_name,
        conversion_scripts=conversion_scripts,
        latest_snapshot=latest_snapshot,
        snapshot_count=snapshot_count,
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
        snapshot_count = 0
        if task.report:
            play_count = task.report.play_count
            comment_count = task.report.comment_count
            message_count = task.report.message_count
        if task.snapshots:
            snapshot_count = len(task.snapshots)
            latest_snap = task.snapshots[-1]
            play_count = latest_snap.play_count
            comment_count = latest_snap.comment_count
            message_count = latest_snap.message_count

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
            deployed_at=task.deployed_at,
            problem_type=problem_type,
            problem_desc=problem_desc,
            play_count=play_count,
            comment_count=comment_count,
            message_count=message_count,
            snapshot_count=snapshot_count,
        ))

    return history_list


@router.get("/overview", response_model=TaskOverviewOut)
async def get_task_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_start = utc_day_start_naive()
    today_filter = (
        ContentTask.user_id == current_user.id,
        ContentTask.created_at >= today_start,
    )

    today_tasks = await db.scalar(
        select(func.count(ContentTask.id)).where(*today_filter)
    )
    today_published = await db.scalar(
        select(func.count(ContentTask.id)).where(
            *today_filter,
            ContentTask.status.in_(["PUBLISHED", "REPORTED", "DIAGNOSED"]),
        )
    )
    today_pending = await db.scalar(
        select(func.count(ContentTask.id)).where(
            *today_filter,
            ContentTask.status == "PENDING",
        )
    )
    today_swapped = await db.scalar(
        select(func.coalesce(func.sum(ContentTask.swap_count), 0)).where(*today_filter)
    )

    intent_result = await db.execute(
        select(Intent.name, func.count(ContentTask.id))
        .join(Intent, Intent.id == ContentTask.intent_id)
        .where(*today_filter)
        .group_by(Intent.name)
        .order_by(func.count(ContentTask.id).desc(), Intent.name)
    )
    intent_distribution = [
        {"intent_name": intent_name or "", "count": count}
        for intent_name, count in intent_result.all()
    ]

    problem_result = await db.execute(
        select(DiagnosisResult.problem_type, func.count(DiagnosisResult.id))
        .join(ContentTask, ContentTask.id == DiagnosisResult.task_id)
        .where(
            ContentTask.user_id == current_user.id,
            DiagnosisResult.problem_type != "normal",
        )
        .group_by(DiagnosisResult.problem_type)
        .order_by(func.count(DiagnosisResult.id).desc(), DiagnosisResult.problem_type)
    )
    problem_stats = [
        {"problem_type": problem_type, "count": count}
        for problem_type, count in problem_result.all()
    ]
    total_problems = sum(item["count"] for item in problem_stats)

    return TaskOverviewOut(
        today_tasks=today_tasks or 0,
        today_published=today_published or 0,
        today_pending=today_pending or 0,
        today_swapped=today_swapped or 0,
        total_problems=total_problems,
        intent_distribution=intent_distribution,
        problem_stats=problem_stats,
    )


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
            existing = await get_current_task(db, current_user.id, data.platform_id)
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
    platform_result.first()

    return await _build_task_out(db, task)


@router.get("/current", response_model=TaskOut)
async def get_current_task_api(
    platform_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await get_current_task(db, current_user.id, platform_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current task")

    return await _build_task_out(db, task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
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

    return await _build_task_out(db, task)


@router.post("/{task_id}/publish")
async def publish_task(
    task_id: uuid.UUID,
    deploy_data: DeployDateUpdate | None = None,
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

    values = {"status": "PUBLISHED", "published_at": utc_now_naive()}
    if deploy_data and deploy_data.deployed_at:
        values["deployed_at"] = deploy_data.deployed_at

    await db.execute(
        update(ContentTask)
        .where(ContentTask.id == task_id)
        .values(**values)
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

    today_start = utc_day_start_naive()

    swap_count_today = 0
    if task.created_at and task.created_at >= today_start:
        swap_count_today = task.swap_count

    if not settings.DEV_MODE and swap_count_today >= 1:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日换条次数已用",
        )

    # 先将旧任务标记为 SWAPPED，避免 generate_task 的 pending 检查冲突
    task.status = "SWAPPED"
    await db.commit()

    try:
        new_task = await generate_task(
            db=db,
            user_id=current_user.id,
            intent_id=task.intent_id,
            platform_id=task.platform_id,
            task_type=task.task_type,
            skip_pending_check=True,  # 换条时跳过 pending 检查，因为旧任务已标记为 SWAPPED
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "HAS_PENDING_TASK":
            # 理论上不会到这里（已标记 SWAPPED），但安全起见恢复旧任务
            task.status = "PENDING"
            await db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Has pending task")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as e:
        # 生成失败，恢复旧任务状态
        task.status = "PENDING"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"换条失败: {str(e)}")

    # 新任务生成成功，删除旧任务
    await db.delete(task)
    new_task.swap_count = swap_count_today + 1
    await db.commit()
    await db.refresh(new_task)

    return await _build_task_out(db, new_task)


@router.post("/{task_id}/report", response_model=ReportResponse, deprecated=True)
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
    data: TaskNextCreate,
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
            platform_id=data.platform_id or task.platform_id,
            task_type=data.task_type or task.task_type,
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
