from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai.persistence.models.document import DocumentStatus


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=50)
    storage_path: str | None = None


class DocumentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    storage_path: str | None
    status: DocumentStatus
    error_message: str | None
    knowledge_base_id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
