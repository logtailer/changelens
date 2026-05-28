"""initial schema placeholder

Revision ID: e3a1b2c4d5f6
Revises:
Create Date: 2026-05-28 10:00:00.000000

"""
from typing import Sequence, Union

revision: str = "e3a1b2c4d5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
