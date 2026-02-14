"""add draft_responses table

Revision ID: cd82b27a17c1
Revises: 003
Create Date: 2026-02-14 09:32:43.945767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cd82b27a17c1'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'draft_responses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('response_type', sa.String(length=30), nullable=False),
        sa.Column('generated_content', sa.Text(), nullable=False),
        sa.Column('edited_content', sa.Text(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_draft_responses_opportunity_id'), 'draft_responses', ['opportunity_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_draft_responses_opportunity_id'), table_name='draft_responses')
    op.drop_table('draft_responses')
