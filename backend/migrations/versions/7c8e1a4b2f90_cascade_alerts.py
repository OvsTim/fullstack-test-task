"""cascade delete alerts with files

Revision ID: 7c8e1a4b2f90
Revises: 0d6439d2e79f
Create Date: 2026-09-12 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "7c8e1a4b2f90"
down_revision: Union[str, Sequence[str], None] = "0d6439d2e79f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_file_id_fkey",
        "alerts",
        "files",
        ["file_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_file_id_fkey",
        "alerts",
        "files",
        ["file_id"],
        ["id"],
    )
