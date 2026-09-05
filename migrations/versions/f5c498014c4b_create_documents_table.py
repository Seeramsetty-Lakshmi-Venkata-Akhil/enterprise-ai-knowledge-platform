"""create documents table

Revision ID: f5c498014c4b
Revises: 6960d37329ef
Create Date: 2026-09-05 15:37:13.251549

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5c498014c4b"
down_revision: str | Sequence[str] | None = "6960d37329ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "completed",
                "failed",
                name="document_status",
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "knowledge_base_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_documents_knowledge_base_id"),
        "documents",
        ["knowledge_base_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_documents_organization_id"),
        "documents",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_documents_organization_id"),
        table_name="documents",
    )

    op.drop_index(
        op.f("ix_documents_knowledge_base_id"),
        table_name="documents",
    )

    op.drop_table("documents")

    sa.Enum(
        "pending",
        "processing",
        "completed",
        "failed",
        name="document_status",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )
