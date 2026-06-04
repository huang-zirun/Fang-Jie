import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.performance_snapshot import PerformanceSnapshot
from app.models.user import User
from app.schemas.performance_snapshot import SnapshotCreate, SnapshotOut, DeployDateUpdate
from app.schemas.report import DiagnosisOut
from app.services.diagnosis_service import diagnose_from_snapshots

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["snapshots"])


@router.post("/{task_id}/snapshots", response_model=SnapshotOut)
async def create_snapshot(
    task_id: uuid.UUID,
    data: SnapshotCreate,
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
    if task.status not in ("PUBLISHED", "DIAGNOSED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be published first")

    snapshot = PerformanceSnapshot(
        task_id=task_id,
        play_count=data.play_count,
        comment_count=data.comment_count,
        message_count=data.message_count,
        source="manual",
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.get("/{task_id}/snapshots", response_model=list[SnapshotOut])
async def list_snapshots(
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

    snap_result = await db.execute(
        select(PerformanceSnapshot)
        .where(PerformanceSnapshot.task_id == task_id)
        .order_by(PerformanceSnapshot.snapshot_at.asc())
    )
    return snap_result.scalars().all()


@router.patch("/{task_id}/deploy")
async def set_deploy_date(
    task_id: uuid.UUID,
    data: DeployDateUpdate,
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

    await db.execute(
        update(ContentTask).where(ContentTask.id == task_id).values(deployed_at=data.deployed_at)
    )
    await db.commit()
    return {"task_id": str(task_id), "deployed_at": data.deployed_at.isoformat() if data.deployed_at else None}


@router.post("/{task_id}/diagnose", response_model=DiagnosisOut)
async def diagnose_task(
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
    if task.status not in ("PUBLISHED", "DIAGNOSED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be published first")

    snap_result = await db.execute(
        select(PerformanceSnapshot)
        .where(PerformanceSnapshot.task_id == task_id)
        .order_by(PerformanceSnapshot.snapshot_at.asc())
    )
    snapshots = snap_result.scalars().all()

    if not snapshots:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No snapshots available. Please report data first.")

    existing_diag_result = await db.execute(
        select(DiagnosisResult).where(DiagnosisResult.task_id == task_id)
    )
    existing_diagnosis = existing_diag_result.scalars().first()
    if existing_diagnosis:
        await db.delete(existing_diagnosis)
        await db.flush()

    diagnosis = await diagnose_from_snapshots(db, task, snapshots)

    new_status = "DIAGNOSED"
    await db.execute(
        update(ContentTask).where(ContentTask.id == task_id).values(
            status=new_status,
            diagnosis_id=diagnosis.id,
        )
    )
    await db.commit()

    return DiagnosisOut(
        problem_type=diagnosis.problem_type,
        problem_desc=diagnosis.problem_desc,
        optimization_direction=diagnosis.optimization_direction,
        optimization_detail=diagnosis.optimization_detail,
        ai_analysis=diagnosis.ai_analysis,
        rule_confidence=diagnosis.rule_confidence,
        snapshot_count=diagnosis.snapshot_count,
        days_since_deploy=diagnosis.days_since_deploy,
        play_trend=diagnosis.play_trend,
        avg_daily_play_growth=diagnosis.avg_daily_play_growth,
    )
