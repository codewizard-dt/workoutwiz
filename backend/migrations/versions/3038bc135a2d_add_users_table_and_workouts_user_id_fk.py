"""add users table and workouts user_id fk

Revision ID: 3038bc135a2d
Revises: 077a1da3f52a
Create Date: 2026-06-04 18:50:20.416902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3038bc135a2d'
down_revision: Union[str, None] = '077a1da3f52a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_foreign_key(
        'fk_workouts_user_id',
        'workouts', 'user',
        ['user_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_workouts_user_id', 'workouts', type_='foreignkey')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
