import uuid
from datetime import datetime

from pydantic import BaseModel


class OptimizationRuleCreate(BaseModel):
    intent_id: uuid.UUID | None = None
    name: str
    problem_type: str
    condition_expr: dict
    optimization_direction: str
    optimization_prompt: str
    priority: int = 0
    is_active: bool = True


class OptimizationRuleOut(BaseModel):
    id: uuid.UUID
    intent_id: uuid.UUID | None = None
    name: str
    problem_type: str
    condition_expr: dict
    optimization_direction: str
    optimization_prompt: str
    priority: int
    is_active: bool
    hit_count: int = 0
    accuracy_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizationRuleUpdate(BaseModel):
    intent_id: uuid.UUID | None = None
    name: str | None = None
    problem_type: str | None = None
    condition_expr: dict | None = None
    optimization_direction: str | None = None
    optimization_prompt: str | None = None
    priority: int | None = None
    is_active: bool | None = None
