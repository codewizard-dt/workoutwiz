"""add_exercise_fields_and_feedback_table

Revision ID: e4a51dde0a60
Revises: 721585857bab
Create Date: 2026-06-06 04:39:06.775249

"""
import json
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4a51dde0a60'
down_revision: Union[str, None] = '721585857bab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- exercise_feedback table ---
    op.create_table('exercise_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workout_set_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('context_type', sa.Enum('exercise', 'set', 'workout', name='feedbackcontexttype'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_exercise_feedback_rating_range'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workout_set_id'], ['workout_sets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exercise_feedback_user_id', 'exercise_feedback', ['user_id'])

    # --- new exercise columns ---
    op.add_column('exercises', sa.Column('joints_loaded', postgresql.ARRAY(sa.String()), server_default=sa.text("'{}'::text[]"), nullable=False))
    op.add_column('exercises', sa.Column('side', sa.String(10), nullable=True))
    op.add_column('exercises', sa.Column('estimated_rep_duration', sa.Float(), nullable=True))

    # --- movement_patterns: JSON -> ARRAY(String) ---
    # asyncpg prepared-statement protocol rejects subqueries in USING expressions,
    # so we use a temp-column swap: add text[] col, copy data, drop json col, rename.
    op.add_column('exercises', sa.Column('movement_patterns_new', postgresql.ARRAY(sa.String()), nullable=True))
    op.execute(sa.text(
        "UPDATE exercises "
        "SET movement_patterns_new = ARRAY(SELECT jsonb_array_elements_text(movement_patterns::jsonb))"
    ))
    op.drop_column('exercises', 'movement_patterns')
    op.alter_column('exercises', 'movement_patterns_new', new_column_name='movement_patterns')
    op.alter_column('exercises', 'movement_patterns', nullable=False, server_default=sa.text("'{}'::text[]"))

    # --- GIN index for joints_loaded ---
    op.create_index(
        'ix_exercises_joints_loaded_gin', 'exercises', ['joints_loaded'],
        postgresql_using='gin'
    )

    # --- data migration: populate joints_loaded, side, estimated_rep_duration from exercises.json ---
    exercises_json = Path(__file__).parents[3] / ".docs" / "guides" / "1-multi-agent" / "exercises.json"
    with open(exercises_json) as f:
        exercises = json.load(f)

    conn = op.get_bind()
    for ex in exercises:
        conn.execute(
            sa.text("""
                UPDATE exercises
                SET joints_loaded = :joints,
                    side = :side,
                    estimated_rep_duration = :erd
                WHERE id = :id
            """),
            {
                "id": str(ex["id"]),
                "joints": ex.get("joints_loaded", []),
                "side": ex.get("side"),
                "erd": ex.get("estimated_rep_duration"),
            }
        )


def downgrade() -> None:
    op.drop_table('exercise_feedback')
    op.execute("DROP TYPE IF EXISTS feedbackcontexttype")
    op.drop_index('ix_exercises_joints_loaded_gin', table_name='exercises')
    op.drop_column('exercises', 'joints_loaded')
    op.drop_column('exercises', 'side')
    op.drop_column('exercises', 'estimated_rep_duration')
    op.add_column('exercises', sa.Column('movement_patterns_old', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.execute(sa.text("UPDATE exercises SET movement_patterns_old = array_to_json(movement_patterns)"))
    op.drop_column('exercises', 'movement_patterns')
    op.alter_column('exercises', 'movement_patterns_old', new_column_name='movement_patterns')
    op.alter_column('exercises', 'movement_patterns', nullable=False, server_default=sa.text("'{}'::json"))
