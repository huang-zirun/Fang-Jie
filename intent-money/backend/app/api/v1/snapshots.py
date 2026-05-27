import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.optimization_rule import OptimizationRule
from app.models.performance_snapshot import PerformanceSnapshot
from app.models.platform import Platform
from app.models.user import User
from app.schemas.performance_snapshot import SnapshotCreate, SnapshotOut, DeployDateUpdate
from app.schemas.report import DiagnosisOut
from app.services.diagnosis_service import diagnose_from_snapshots
from app.utils.time import utc_now_naive

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


@router.post("/{task_id}/snapshots/fetch", response_model=SnapshotOut)
async def fetch_snapshot_via_cdp(
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

    if not settings.CDP_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="CDP is not enabled")

    platform_result = await db.execute(
        select(Platform).where(Platform.id == task.platform_id)
    )
    platform = platform_result.scalars().first()
    platform_name = platform.name.lower() if platform else ""

    try:
        from app.services.platform_scraper.cdp_browser import CdpBrowser
        browser = CdpBrowser(
            host=settings.CDP_DEBUG_HOST,
            port=settings.CDP_DEBUG_PORT,
            scheme=settings.CDP_DEBUG_SCHEME,
        )

        if not await browser.check_health():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="CDP connection unavailable")

        play_count = 0
        comment_count = 0
        message_count = 0

        if "抖音" in platform_name or "douyin" in platform_name:
            play_count, comment_count, message_count = await _fetch_douyin_stats(browser, task)
        elif "小红书" in platform_name or "xhs" in platform_name or "xiaohongshu" in platform_name:
            play_count, comment_count, message_count = await _fetch_xhs_stats(browser, task)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported platform: {platform_name}")

        await browser.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CDP fetch error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CDP data fetch failed: {str(e)}")

    snapshot = PerformanceSnapshot(
        task_id=task_id,
        play_count=play_count,
        comment_count=comment_count,
        message_count=message_count,
        source="cdp_manual",
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def _fetch_douyin_stats(browser, task: ContentTask) -> tuple[int, int, int]:
    creator_url = "https://creator.douyin.com/creator-micro/content/manage"
    await browser.navigate(creator_url, wait_seconds=5.0)

    raw = await browser.evaluate("""
    (function() {
        var items = document.querySelectorAll('[class*="content-item"], [class*="video-item"], [class*="work-item"]');
        var result = {play_count: 0, comment_count: 0, message_count: 0};
        if (items.length > 0) {
            var first = items[0];
            var spans = first.querySelectorAll('span, [class*="count"], [class*="num"]');
            var nums = [];
            spans.forEach(function(s) {
                var t = s.textContent.trim();
                if (/^[\\d.]+万?$/.test(t)) nums.push(t);
            });
            if (nums.length >= 1) result.play_count = nums[0];
            if (nums.length >= 2) result.comment_count = nums[1];
        }
        return JSON.stringify(result);
    })()
    """)

    play_count = 0
    comment_count = 0
    message_count = 0

    if raw:
        import json
        try:
            data = json.loads(raw)
            play_count = _parse_count_str(data.get("play_count", "0"))
            comment_count = _parse_count_str(data.get("comment_count", "0"))
            message_count = _parse_count_str(data.get("message_count", "0"))
        except (json.JSONDecodeError, TypeError):
            pass

    return play_count, comment_count, message_count


async def _fetch_xhs_stats(browser, task: ContentTask) -> tuple[int, int, int]:
    creator_url = "https://creator.xiaohongshu.com/publish/publish?source=note"
    await browser.navigate(creator_url, wait_seconds=5.0)

    raw = await browser.evaluate("""
    (function() {
        var result = {play_count: 0, comment_count: 0, message_count: 0};
        var items = document.querySelectorAll('[class*="note-item"], [class*="content-item"]');
        if (items.length > 0) {
            var first = items[0];
            var spans = first.querySelectorAll('span, [class*="count"], [class*="num"]');
            var nums = [];
            spans.forEach(function(s) {
                var t = s.textContent.trim();
                if (/^[\\d.]+万?$/.test(t)) nums.push(t);
            });
            if (nums.length >= 1) result.play_count = nums[0];
            if (nums.length >= 2) result.comment_count = nums[1];
        }
        return JSON.stringify(result);
    })()
    """)

    play_count = 0
    comment_count = 0
    message_count = 0

    if raw:
        import json
        try:
            data = json.loads(raw)
            play_count = _parse_count_str(data.get("play_count", "0"))
            comment_count = _parse_count_str(data.get("comment_count", "0"))
            message_count = _parse_count_str(data.get("message_count", "0"))
        except (json.JSONDecodeError, TypeError):
            pass

    return play_count, comment_count, message_count


def _parse_count_str(value) -> int:
    if isinstance(value, int):
        return value
    if not value:
        return 0
    s = str(value).strip()
    if "万" in s:
        return int(float(s.replace("万", "")) * 10000)
    try:
        return int(s)
    except ValueError:
        return 0


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
