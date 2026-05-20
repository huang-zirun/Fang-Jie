import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.content_structure import ContentStructure
from app.models.user import User
from app.schemas.content_structure import (
    ContentStructureCreate,
    ContentStructureOut,
    ContentStructureUpdate,
)

router = APIRouter(prefix="/content-structures", tags=["content_structures"])


@router.get("", response_model=list[ContentStructureOut])
async def list_structures(
    intent_id: uuid.UUID | None = None,
    platform_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentStructure).order_by(ContentStructure.priority.desc())
    if intent_id:
        query = query.where(ContentStructure.intent_id == intent_id)
    if platform_id:
        query = query.where(ContentStructure.platform_id == platform_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{structure_id}", response_model=ContentStructureOut)
async def get_structure(structure_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentStructure).where(ContentStructure.id == structure_id))
    structure = result.scalars().first()
    if not structure:
        raise HTTPException(status_code=404, detail="Content structure not found")
    return structure


@router.post("", response_model=ContentStructureOut)
async def create_structure(
    data: ContentStructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    structure = ContentStructure(**data.model_dump(), is_active=True)
    db.add(structure)
    await db.commit()
    await db.refresh(structure)
    return structure


@router.put("/{structure_id}", response_model=ContentStructureOut)
async def update_structure(
    structure_id: uuid.UUID,
    data: ContentStructureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ContentStructure).where(ContentStructure.id == structure_id))
    structure = result.scalars().first()
    if not structure:
        raise HTTPException(status_code=404, detail="Content structure not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(structure, key, value)

    await db.commit()
    await db.refresh(structure)
    return structure


@router.delete("/{structure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_structure(
    structure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ContentStructure).where(ContentStructure.id == structure_id))
    structure = result.scalars().first()
    if not structure:
        raise HTTPException(status_code=404, detail="Content structure not found")
    await db.delete(structure)
    await db.commit()
