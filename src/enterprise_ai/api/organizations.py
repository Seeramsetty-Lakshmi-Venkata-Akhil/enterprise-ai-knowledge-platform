from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.organization import Organization
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from enterprise_ai.schemas.user import UserResponse

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: OrganizationCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Organization:
    organization = Organization(
        name=payload.name,
    )

    session.add(organization)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization already exists",
        ) from exc

    await session.refresh(organization)

    return organization


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def get_organization(
    organization_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Organization:
    organization = await session.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.get(
    "",
    response_model=list[OrganizationResponse],
)
async def list_organizations(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Organization]:
    result = await session.execute(select(Organization).order_by(Organization.created_at.desc()))

    return list(result.scalars().all())


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Organization:
    organization = await session.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if payload.name is not None:
        organization.name = payload.name

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization already exists",
        ) from exc

    await session.refresh(organization)

    return organization


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization(
    organization_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    organization = await session.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    await session.delete(organization)
    await session.commit()


@router.get(
    "/{organization_id}/users",
    response_model=list[UserResponse],
)
async def list_organization_users(
    organization_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[User]:
    organization = await session.get(
        Organization,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    result = await session.execute(
        select(User)
        .where(User.organization_id == organization_id)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())
