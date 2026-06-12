# 109 — coach_draft persistence: draft | approved | sent status on AI-generated recommendations

> **Depends on**: none
> **Blocks**: [110-coach-draft-lifecycle-endpoint](110-coach-draft-lifecycle-endpoint.md)
> **Parallel-safe with**: [105-accountability-service](105-accountability-service.md), [106-coach-nudge-endpoint](106-coach-nudge-endpoint.md), [107-coach-page-action-items](107-coach-page-action-items.md)

## Objective

Create the `coach_drafts` PostgreSQL table and SQLAlchemy model to persist AI-generated recommendations and nudge messages with a `draft | approved | sent` lifecycle status. This is the HITL persistence layer for Phase 2 of Roadmap 007.

## Approach

A new SQLAlchemy model `CoachDraft` in `backend/app/models/coach_draft.py` backed by a `coach_drafts` table. Status is a PostgreSQL `ENUM` type with three values: `draft`, `approved`, `sent`. The model stores the draft body, the member it is addressed to, the content type (`nudge` | `recommendation`), and the approval trail (approved_by, approved_at). An Alembic migration creates the table.

The `AuditLogEntry` pattern in `backend/app/models/audit_log.py` is the reference for model structure and Alembic migration format.

## Steps

### 1. Create `backend/app/models/coach_draft.py`  <!-- agent: general-purpose -->

```python
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..database import Base


class CoachDraftStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class CoachDraftContentType(str, enum.Enum):
    nudge = "nudge"
    recommendation = "recommendation"


class CoachDraft(Base):
    __tablename__ = "coach_drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    member_name: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[CoachDraftContentType] = mapped_column(
        SAEnum(CoachDraftContentType, name="coachdraftcontenttype", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    grounded_on: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialised list[str]
    status: Mapped[CoachDraftStatus] = mapped_column(
        SAEnum(CoachDraftStatus, name="coachdraftstatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CoachDraftStatus.draft,
        index=True,
    )
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)   # user email
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
```

- [x] `backend/app/models/coach_draft.py` exists with `CoachDraft`, `CoachDraftStatus`, `CoachDraftContentType` <!-- Completed: 2026-06-11 -->
- [x] Status enum has exactly three values: `draft`, `approved`, `sent` <!-- Completed: 2026-06-11 -->
- [x] Content type enum has two values: `nudge`, `recommendation` <!-- Completed: 2026-06-11 -->

### 2. Register `CoachDraft` in `backend/app/models/__init__.py`  <!-- agent: general-purpose -->

Use Serena `search_for_pattern` to see what the current `__init__.py` imports. Add:

```python
from .coach_draft import CoachDraft, CoachDraftStatus, CoachDraftContentType
```

- [x] `CoachDraft` is imported in `backend/app/models/__init__.py` <!-- Completed: 2026-06-11 -->

### 3. Create Alembic migration  <!-- agent: general-purpose -->

Get the current head revision by running: `cd backend && python -m alembic heads` (capture output).

Create `backend/migrations/versions/d1e2f3a4b5c6_add_coach_drafts_table.py`:

```python
"""add_coach_drafts_table

Revision ID: d1e2f3a4b5c6
Revises: a1b2c3d4e5f6
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE coachdraftstatus AS ENUM ('draft', 'approved', 'sent')")
    op.execute("CREATE TYPE coachdraftcontenttype AS ENUM ('nudge', 'recommendation')")
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
```

**Important**: check the actual head revision first — replace `'a1b2c3d4e5f6'` in `down_revision` with the real current head (run `cd backend && python -m alembic heads` to find it).

- [x] Migration file exists at `backend/migrations/versions/d1e2f3a4b5c6_add_coach_drafts_table.py` <!-- Completed: 2026-06-11 -->
- [x] `down_revision` points to the actual current Alembic head (`b2c3d4e5f6a7`) <!-- Completed: 2026-06-11 -->
- [x] `upgrade()` creates both ENUM types and the table <!-- Completed: 2026-06-11 -->
- [x] `downgrade()` drops table and ENUM types <!-- Completed: 2026-06-11 -->

### 4. Run the migration  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a
cd backend && python -m alembic upgrade head
```

Verify success: `python -m alembic current` should show `d1e2f3a4b5c6 (head)`.

- [x] Migration runs successfully (no errors) <!-- Completed: 2026-06-11 -->
- [x] `coach_drafts` table exists in the database after migration <!-- Completed: 2026-06-11 -->

### 5. Add `CoachDraftSchema` Pydantic models to `backend/app/schemas/coach.py`  <!-- agent: general-purpose -->

Using Serena `insert_after_symbol` after `NudgeResponse`:

```python
class CoachDraftSchema(BaseModel):
    id: str
    member_id: str
    member_name: str
    content_type: str
    body: str
    grounded_on: list[str]
    status: str
    created_by: str | None
    approved_by: str | None
    approved_at: str | None
    sent_at: str | None
    created_at: str

    model_config = {"from_attributes": True}
```

- [x] `CoachDraftSchema` class exists in `backend/app/schemas/coach.py` <!-- Completed: 2026-06-11 -->

## Acceptance Criteria

- [x] `backend/app/models/coach_draft.py` exists with `CoachDraft` SQLAlchemy model <!-- Completed: 2026-06-11 -->
- [x] `CoachDraftStatus` enum has values `draft`, `approved`, `sent` <!-- Completed: 2026-06-11 -->
- [x] `CoachDraftContentType` enum has values `nudge`, `recommendation` <!-- Completed: 2026-06-11 -->
- [x] Alembic migration applies cleanly: `python -m alembic upgrade head` exits 0 <!-- Completed: 2026-06-11 -->
- [x] `coach_drafts` table has columns: `id`, `member_id`, `member_name`, `content_type`, `body`, `grounded_on`, `status`, `created_by`, `approved_by`, `approved_at`, `sent_at`, `created_at`, `updated_at` <!-- Completed: 2026-06-11 -->
- [x] `CoachDraftSchema` Pydantic model exists in `backend/app/schemas/coach.py` <!-- Completed: 2026-06-11 -->

---
**UAT**: [`.docs/uat/completed/109-coach-draft-persistence.uat.md`](../uat/completed/109-coach-draft-persistence.uat.md)
