"""exam submissions

Revision ID: e9ec8c889fb8
Revises: 28bf5095bd2a
Create Date: 2026-10-29 13:42:03.010348

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e9ec8c889fb8"
down_revision: str | None = "28bf5095bd2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exam_submissions",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("certification_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Enum("test", "video", name="exam_kind"), nullable=False),
        sa.Column(
            "source",
            sa.Enum("examportal", "wetransfer", "email", "other", name="exam_source"),
            nullable=False,
        ),
        sa.Column("link_url", sa.String(length=1000), nullable=True),
        sa.Column("link_expires_on", sa.Date(), nullable=True),
        sa.Column("saved_url", sa.String(length=1000), nullable=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "received",
                "in_review",
                "on_hold",
                "corrected",
                "notified",
                "cancelled",
                name="exam_status",
            ),
            nullable=False,
        ),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column(
            "outcome", sa.Enum("passed", "failed", "resubmit", name="exam_outcome"), nullable=True
        ),
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("feedback_md", sa.Text(), server_default="", nullable=False),
        sa.Column("corrected_by_id", sa.Uuid(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint(
            "due_on >= received_on", name=op.f("ck_exam_submissions_due_after_received")
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 10", name=op.f("ck_exam_submissions_score_in_range")
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name=op.f("fk_exam_submissions_assignee_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["certification_id"],
            ["certifications.id"],
            name=op.f("fk_exam_submissions_certification_id_certifications"),
        ),
        sa.ForeignKeyConstraint(
            ["corrected_by_id"],
            ["users.id"],
            name=op.f("fk_exam_submissions_corrected_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_exam_submissions_created_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("fk_exam_submissions_student_id_students")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_submissions")),
    )
    op.create_index(
        "ix_exam_submissions_assignee_id", "exam_submissions", ["assignee_id"], unique=False
    )
    op.create_index(
        "ix_exam_submissions_status_due_on", "exam_submissions", ["status", "due_on"], unique=False
    )
    op.create_index(
        "ix_exam_submissions_student_id", "exam_submissions", ["student_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_exam_submissions_student_id", table_name="exam_submissions")
    op.drop_index("ix_exam_submissions_status_due_on", table_name="exam_submissions")
    op.drop_index("ix_exam_submissions_assignee_id", table_name="exam_submissions")
    op.drop_table("exam_submissions")
    sa.Enum(name="exam_outcome").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="exam_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="exam_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="exam_kind").drop(op.get_bind(), checkfirst=True)
