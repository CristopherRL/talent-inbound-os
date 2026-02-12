"""create interactions table

Revision ID: 003
Revises: 002
Create Date: 2026-02-12 12:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('interactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('sanitized_content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=30), nullable=False),
        sa.Column('interaction_type', sa.String(length=20), nullable=False, server_default='INITIAL'),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('classification', sa.String(length=20), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('pipeline_log', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interactions_candidate_id'), 'interactions', ['candidate_id'])
    op.create_index(op.f('ix_interactions_opportunity_id'), 'interactions', ['opportunity_id'])
    op.create_index(op.f('ix_interactions_content_hash'), 'interactions', ['content_hash'])


def downgrade() -> None:
    op.drop_index(op.f('ix_interactions_content_hash'), table_name='interactions')
    op.drop_index(op.f('ix_interactions_opportunity_id'), table_name='interactions')
    op.drop_index(op.f('ix_interactions_candidate_id'), table_name='interactions')
    op.drop_table('interactions')
