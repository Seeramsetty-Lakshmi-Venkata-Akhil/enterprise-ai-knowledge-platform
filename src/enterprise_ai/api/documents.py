from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.document import Document
from enterprise_ai.persistence.models.knowledge_base import KnowledgeBase
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


router = APIRouter(
    prefix="/knowledge-bases/{knowledge_base_id}/documents",
    tags=["documents"],
)


async def get_authorized_knowledge_base(
    knowledge_base_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> KnowledgeBase:
    knowledge_base = await session.get(
        KnowledgeBase,
        knowledge_base_id,
    )

    if knowledge_base is None or knowledge_base.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    return knowledge_base


async def get_authorized_document(
    document_id: UUID,
    knowledge_base_id: UUID,
    organization_id: UUID,
    session: AsyncSession,
) -> Document:
    statement = select(Document).where(
        Document.id == document_id,
        Document.knowledge_base_id == knowledge_base_id,
        Document.organization_id == organization_id,
    )

    result = await session.execute(statement)
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    knowledge_base_id: UUID,
    payload: DocumentCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> Document:
    knowledge_base = await get_authorized_knowledge_base(
        knowledge_base_id,
        session,
        current_user,
    )

    document = Document(
        name=payload.name,
        source_type=payload.source_type,
        storage_path=payload.storage_path,
        knowledge_base_id=knowledge_base.id,
        organization_id=current_user.organization_id,
    )

    session.add(document)
    await session.commit()
    await session.refresh(document)

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents(
    knowledge_base_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Document]:
    await get_authorized_knowledge_base(
        knowledge_base_id,
        session,
        current_user,
    )

    statement = (
        select(Document)
        .where(
            Document.knowledge_base_id == knowledge_base_id,
            Document.organization_id == current_user.organization_id,
        )
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    knowledge_base_id: UUID,
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> Document:
    await get_authorized_knowledge_base(
        knowledge_base_id,
        session,
        current_user,
    )

    return await get_authorized_document(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id,
        organization_id=current_user.organization_id,
        session=session,
    )


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def update_document(
    knowledge_base_id: UUID,
    document_id: UUID,
    payload: DocumentUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> Document:
    await get_authorized_knowledge_base(
        knowledge_base_id,
        session,
        current_user,
    )

    document = await get_authorized_document(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id,
        organization_id=current_user.organization_id,
        session=session,
    )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(document, field, value)

    await session.commit()
    await session.refresh(document)

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    knowledge_base_id: UUID,
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> None:
    await get_authorized_knowledge_base(
        knowledge_base_id,
        session,
        current_user,
    )

    document = await get_authorized_document(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id,
        organization_id=current_user.organization_id,
        session=session,
    )

    await session.delete(document)
    await session.commit()
