import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enterprise_ai.persistence.base import Base

if TYPE_CHECKING:
    from enterprise_ai.persistence.models.user import User


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="organization",
    )

    knowledge_bases = relationship(
        "KnowledgeBase",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
