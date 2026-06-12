"""add_coach_drafts_table

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a7
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'coach_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', sa.String(), nullable=False),
        sa.Column('member_name', sa.String(), nullable=False),
        sa.Column('content_type', sa.Enum('nudge', 'recommendation', name='coachdraftcontenttype'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('grounded_on', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'approved', 'sent', name='coachdraftstatus'), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_coach_drafts_member_id', 'coach_drafts', ['member_id'])
    op.create_index('ix_coach_drafts_status', 'coach_drafts', ['status'])


def downgrade() -> None:
    op.drop_index('ix_coach_drafts_status', table_name='coach_drafts')
    op.drop_index('ix_coach_drafts_member_id', table_name='coach_drafts')
    op.drop_table('coach_drafts')
    op.execute("DROP TYPE IF EXISTS coachdraftcontenttype")
    op.execute("DROP TYPE IF EXISTS coachdraftstatus")
