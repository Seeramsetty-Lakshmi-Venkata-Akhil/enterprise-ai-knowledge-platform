from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
