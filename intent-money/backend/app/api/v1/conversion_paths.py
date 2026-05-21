import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.conversion_path import ConversionPath
from app.models.user import User
from app.schemas.conversion_path import (
    ConversionPathCreate,
    ConversionPathOut,
    ConversionPathUpdate,
)

router = APIRouter(prefix="/conversion-paths", tags=["conversion_paths"])


@router.get("", response_model=list[ConversionPathOut])
async def list_conversion_paths(
    intent_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ConversionPath).order_by(ConversionPath.sort_order.asc(), ConversionPath.created_at.asc())
    if intent_id:
        query = query.where(ConversionPath.intent_id == intent_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ConversionPathOut)
async def create_conversion_path(
    data: ConversionPathCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = ConversionPath(**data.model_dump())
    db.add(path)
    await db.commit()
    await db.refresh(path)
    return path


@router.put("/{path_id}", response_model=ConversionPathOut)
async def update_conversion_path(
    path_id: uuid.UUID,
    data: ConversionPathUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ConversionPath).where(ConversionPath.id == path_id))
    path = result.scalars().first()
    if not path:
        raise HTTPException(status_code=404, detail="Conversion path not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(path, key, value)

    await db.commit()
    await db.refresh(path)
    return path


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversion_path(
    path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ConversionPath).where(ConversionPath.id == path_id))
    path = result.scalars().first()
    if not path:
        raise HTTPException(status_code=404, detail="Conversion path not found")
    await db.delete(path)
    await db.commit()
