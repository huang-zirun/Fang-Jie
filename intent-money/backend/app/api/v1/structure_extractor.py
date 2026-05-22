import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.content_structure import ContentStructure
from app.models.extracted_structure import ExtractedStructure
from app.models.platform import Platform
from app.models.user import User
from app.schemas.structure_extractor import ExtractRequest, ExtractResponse
from app.services.structure_extractor import extract_structure_from_url

router = APIRouter(prefix="/admin", tags=["structure_extractor"])


@router.post("/extract-structure", response_model=ExtractResponse)
async def extract_structure(
    data: ExtractRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    platform_name_map = {"douyin": "抖音", "xhs": "小红书"}
    platform_name = platform_name_map.get(data.platform)
    if not platform_name:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {data.platform}")

    result = await db.execute(select(Platform).where(Platform.name == platform_name))
    platform = result.scalars().first()
    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform '{platform_name}' not found")

    extraction = await extract_structure_from_url(data.url, data.platform)
    if extraction is None:
        raise HTTPException(status_code=500, detail="Failed to extract structure from URL")

    record = ExtractedStructure(
        source_url=data.url,
        platform_id=platform.id,
        hook_type=extraction.get("hook_type", "未知型"),
        emotion_structure=extraction.get("emotion_structure", {"type": "unknown", "flow": ""}),
        conversion_structure=extraction.get("conversion_structure", {"type": "unknown", "flow": ""}),
        key_elements=extraction.get("key_elements", []),
        viral_score=extraction.get("viral_score", 0),
        analysis_summary=extraction.get("analysis_summary", ""),
        status="pending",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/extracted-structures", response_model=list[ExtractResponse])
async def list_extracted_structures(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(ExtractedStructure).order_by(ExtractedStructure.created_at.desc())
    if status_filter:
        query = query.where(ExtractedStructure.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/extracted-structures/{structure_id}/approve", response_model=ExtractResponse)
async def approve_extracted_structure(
    structure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(ExtractedStructure).where(ExtractedStructure.id == structure_id))
    extracted = result.scalars().first()
    if not extracted:
        raise HTTPException(status_code=404, detail="Extracted structure not found")

    if extracted.status != "pending":
        raise HTTPException(status_code=400, detail=f"Structure already {extracted.status}")

    content_structure = ContentStructure(
        intent_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        platform_id=extracted.platform_id,
        hook_type=extracted.hook_type,
        emotion_structure=extracted.emotion_structure,
        conversion_structure=extracted.conversion_structure,
        prompt_template=f"基于爆款分析提取：钩子类型={extracted.hook_type}，情绪结构={extracted.emotion_structure.get('type', '')}，转化结构={extracted.conversion_structure.get('type', '')}",
        fallback_content={
            "key_elements": extracted.key_elements,
            "analysis_summary": extracted.analysis_summary,
            "source_url": extracted.source_url,
        },
        priority=extracted.viral_score,
        market_score=float(extracted.viral_score),
        is_active=True,
    )
    db.add(content_structure)

    extracted.status = "approved"
    extracted.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(extracted)
    return extracted
