"""add_enjoyment_note_to_workouts

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-06 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("enjoyment", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "note")
    op.drop_column("workouts", "enjoyment")
