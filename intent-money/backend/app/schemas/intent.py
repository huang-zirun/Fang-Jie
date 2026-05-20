import uuid

from pydantic import BaseModel


class IntentOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}
