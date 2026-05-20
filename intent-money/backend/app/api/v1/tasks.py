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
from app.models.performance_report import PerformanceReport
from app.models.platform import Platform
from app.schemas.report import ReportCreate, ReportResponse, DiagnosisOut as DiagnosisResultOut
from app.schemas.task import TaskCreate, TaskOut
from app.services.diagnosis_service import diagnose_performance
from app.services.task_service import generate_task, get_current_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


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
                platform_result = await db.execute(
                    Platform.__table__.select().where(Platform.id == existing.platform_id)
                )
                platform_row = platform_result.first()
                return TaskOut(
                    id=existing.id,
                    platform_name=platform_row.name if platform_row else "",
                    hook_text=existing.hook_text,
                    storyboard=existing.storyboard,
                    script_text=existing.script_text,
                    title=existing.title,
                    comment_template=existing.comment_template,
                    why_it_works=existing.why_it_works,
                    is_optimized=existing.is_optimized,
                    optimization_note=existing.optimization_note,
                    prev_task_id=existing.prev_task_id,
                    created_at=existing.created_at,
                )
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
    )


@router.get("/current", response_model=TaskOut)
async def get_current_task_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await get_current_task(db, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current task")

    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == task.platform_id)
    )
    platform_row = platform_result.first()

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
    )


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

    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == new_task.platform_id)
    )
    platform_row = platform_result.first()

    return TaskOut(
        id=new_task.id,
        platform_name=platform_row.name if platform_row else "",
        hook_text=new_task.hook_text,
        storyboard=new_task.storyboard,
        script_text=new_task.script_text,
        title=new_task.title,
        comment_template=new_task.comment_template,
        why_it_works=new_task.why_it_works,
        is_optimized=new_task.is_optimized,
        optimization_note=new_task.optimization_note,
        prev_task_id=new_task.prev_task_id,
        created_at=new_task.created_at,
    )


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

    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == new_task.platform_id)
    )
    platform_row = platform_result.first()

    return TaskOut(
        id=new_task.id,
        platform_name=platform_row.name if platform_row else "",
        hook_text=new_task.hook_text,
        storyboard=new_task.storyboard,
        script_text=new_task.script_text,
        title=new_task.title,
        comment_template=new_task.comment_template,
        why_it_works=new_task.why_it_works,
        is_optimized=new_task.is_optimized,
        optimization_note=new_task.optimization_note,
        prev_task_id=new_task.prev_task_id,
        created_at=new_task.created_at,
    )
