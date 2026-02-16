"""rename status to stage and migrate opportunity lifecycle model

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename column: opportunities.status → opportunities.stage
    op.alter_column('opportunities', 'status', new_column_name='stage')

    # 2. Migrate existing status values to new stage values
    op.execute(
        "UPDATE opportunities SET stage = 'DISCOVERY' "
        "WHERE stage IN ('NEW', 'ANALYZING', 'ACTION_REQUIRED')"
    )
    op.execute(
        "UPDATE opportunities SET stage = 'ENGAGING' "
        "WHERE stage = 'REVIEWING'"
    )
    # INTERVIEWING, OFFER, REJECTED, GHOSTED remain the same

    # 3. Add new columns for stage suggestions
    op.add_column(
        'opportunities',
        sa.Column('suggested_stage', sa.String(30), nullable=True),
    )
    op.add_column(
        'opportunities',
        sa.Column('suggested_stage_reason', sa.Text(), nullable=True),
    )

    # 4. Rename status_transitions table → stage_transitions
    op.rename_table('status_transitions', 'stage_transitions')

    # 5. Rename columns in stage_transitions
    op.alter_column('stage_transitions', 'from_status', new_column_name='from_stage')
    op.alter_column('stage_transitions', 'to_status', new_column_name='to_stage')

    # 6. Migrate transition data to new stage values
    op.execute(
        "UPDATE stage_transitions SET from_stage = 'DISCOVERY' "
        "WHERE from_stage IN ('NEW', 'ANALYZING', 'ACTION_REQUIRED')"
    )
    op.execute(
        "UPDATE stage_transitions SET from_stage = 'ENGAGING' "
        "WHERE from_stage = 'REVIEWING'"
    )
    op.execute(
        "UPDATE stage_transitions SET to_stage = 'DISCOVERY' "
        "WHERE to_stage IN ('NEW', 'ANALYZING', 'ACTION_REQUIRED')"
    )
    op.execute(
        "UPDATE stage_transitions SET to_stage = 'ENGAGING' "
        "WHERE to_stage = 'REVIEWING'"
    )


def downgrade() -> None:
    # Reverse migration data in stage_transitions
    op.execute(
        "UPDATE stage_transitions SET from_stage = 'ACTION_REQUIRED' "
        "WHERE from_stage = 'DISCOVERY'"
    )
    op.execute(
        "UPDATE stage_transitions SET from_stage = 'REVIEWING' "
        "WHERE from_stage = 'ENGAGING'"
    )
    op.execute(
        "UPDATE stage_transitions SET to_stage = 'ACTION_REQUIRED' "
        "WHERE to_stage = 'DISCOVERY'"
    )
    op.execute(
        "UPDATE stage_transitions SET to_stage = 'REVIEWING' "
        "WHERE to_stage = 'ENGAGING'"
    )

    # Rename columns back
    op.alter_column('stage_transitions', 'from_stage', new_column_name='from_status')
    op.alter_column('stage_transitions', 'to_stage', new_column_name='to_status')

    # Rename table back
    op.rename_table('stage_transitions', 'status_transitions')

    # Drop new columns
    op.drop_column('opportunities', 'suggested_stage_reason')
    op.drop_column('opportunities', 'suggested_stage')

    # Reverse data migration
    op.execute(
        "UPDATE opportunities SET stage = 'ACTION_REQUIRED' "
        "WHERE stage = 'DISCOVERY'"
    )
    op.execute(
        "UPDATE opportunities SET stage = 'REVIEWING' "
        "WHERE stage = 'ENGAGING'"
    )

    # Rename column back
    op.alter_column('opportunities', 'stage', new_column_name='status')
