"""add_audit_log_table

Revision ID: a1b2c3d4e5f6
Revises: e4a51dde0a60
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e4a51dde0a60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_in', sa.Integer(), nullable=True),
        sa.Column('tokens_out', sa.Integer(), nullable=True),
        sa.Column('route', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('node_name', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('source_id', sa.Text(), nullable=True),
        sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_session_id', 'audit_log', ['session_id'])
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_event', 'audit_log', ['event'])


def downgrade() -> None:
    op.drop_index('ix_audit_log_event', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    op.drop_index('ix_audit_log_session_id', table_name='audit_log')
    op.drop_table('audit_log')
