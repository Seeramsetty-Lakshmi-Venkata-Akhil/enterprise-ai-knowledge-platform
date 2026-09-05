from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.knowledge_base import KnowledgeBase
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["knowledge-bases"],
)


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        organization_id=current_user.organization_id,
    )

    session.add(knowledge_base)
    await session.commit()
    await session.refresh(knowledge_base)

    return knowledge_base


@router.get(
    "",
    response_model=list[KnowledgeBaseResponse],
)
async def list_knowledge_bases(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[KnowledgeBase]:
    result = await session.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.organization_id == current_user.organization_id)
        .order_by(KnowledgeBase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
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


@router.patch(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
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

    if payload.name is not None:
        knowledge_base.name = payload.name

    if payload.description is not None:
        knowledge_base.description = payload.description

    await session.commit()
    await session.refresh(knowledge_base)

    return knowledge_base


@router.delete(
    "/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    knowledge_base = await session.get(
        KnowledgeBase,
        knowledge_base_id,
    )

    if knowledge_base is None or knowledge_base.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    await session.delete(knowledge_base)
    await session.commit()
