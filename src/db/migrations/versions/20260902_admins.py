"""admins

Revision ID: a1b2c3d4e5f6
Revises: 912c996d627a
Create Date: 2026-09-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "912c996d627a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("added_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("admins")
