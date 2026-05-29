"""full schema

Revision ID: f4e3d2c1b0a9
Revises: e3a1b2c4d5f6
Create Date: 2026-05-29 09:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4e3d2c1b0a9"
down_revision: Union[str, None] = "e3a1b2c4d5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE role AS ENUM ('admin', 'operator', 'viewer', 'auditor')")
    op.execute(
        "CREATE TYPE eventtype AS ENUM "
        "('deployment', 'config_change', 'incident', 'rollback', 'annotation', 'generic')"
    )
    op.execute(
        "CREATE TYPE sourcesystem AS ENUM "
        "('github_actions', 'alertmanager', 'kubernetes', 'pagerduty', 'manual', 'generic')"
    )
    op.execute("CREATE TYPE severity AS ENUM ('critical', 'high', 'medium', 'low')")
    op.execute(
        "CREATE TYPE incidentstatus AS ENUM ('open', 'resolved', 'investigating')"
    )

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "operator", "viewer", "auditor", name="role"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "incidents",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "severity",
            sa.Enum("critical", "high", "medium", "low", name="severity"),
            nullable=False,
        ),
        sa.Column("source_system", sa.String()),
        sa.Column("external_id", sa.String()),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", "investigating", name="incidentstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_incidents_service", "incidents", ["service"])

    op.create_table(
        "change_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "deployment",
                "config_change",
                "incident",
                "rollback",
                "annotation",
                "generic",
                name="eventtype",
            ),
            nullable=False,
        ),
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("cluster", sa.String()),
        sa.Column("region", sa.String()),
        sa.Column("version", sa.String()),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column(
            "source_system",
            sa.Enum(
                "github_actions",
                "alertmanager",
                "kubernetes",
                "pagerduty",
                "manual",
                "generic",
                name="sourcesystem",
            ),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("raw_payload", postgresql.JSONB()),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.incident_id"),
        ),
        sa.Column("checksum", sa.Text()),
    )
    op.create_index("ix_change_events_service", "change_events", ["service"])
    op.create_index("ix_change_events_environment", "change_events", ["environment"])
    op.create_index("ix_change_events_timestamp", "change_events", ["timestamp"])
    op.create_index(
        "ix_change_events_service_env_ts",
        "change_events",
        ["service", "environment", "timestamp"],
    )

    op.create_table(
        "annotations",
        sa.Column("annotation_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("change_events.event_id"),
        ),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.incident_id"),
        ),
        sa.Column("service", sa.String()),
        sa.Column("environment", sa.String()),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "author",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("annotations")
    op.drop_table("change_events")
    op.drop_table("incidents")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS severity")
    op.execute("DROP TYPE IF EXISTS sourcesystem")
    op.execute("DROP TYPE IF EXISTS eventtype")
    op.execute("DROP TYPE IF EXISTS role")
