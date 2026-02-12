"""create opportunities and status_transitions tables

Revision ID: 002
Revises: f01db71198fd
Create Date: 2026-02-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = 'f01db71198fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Opportunities table
    op.create_table('opportunities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('client_name', sa.String(length=255), nullable=True),
        sa.Column('role_title', sa.String(length=255), nullable=True),
        sa.Column('salary_range', sa.String(length=100), nullable=True),
        sa.Column('tech_stack', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('work_model', sa.String(length=20), nullable=True),
        sa.Column('recruiter_name', sa.String(length=255), nullable=True),
        sa.Column('recruiter_type', sa.String(length=30), nullable=True),
        sa.Column('recruiter_company', sa.String(length=255), nullable=True),
        sa.Column('match_score', sa.Integer(), nullable=True),
        sa.Column('match_reasoning', sa.Text(), nullable=True),
        sa.Column('missing_fields', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='NEW'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_opportunities_candidate_id'), 'opportunities', ['candidate_id'])
    op.create_index(op.f('ix_opportunities_status'), 'opportunities', ['status'])
    op.create_index(op.f('ix_opportunities_last_interaction_at'), 'opportunities', ['last_interaction_at'])

    # Status transitions table
    op.create_table('status_transitions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=False),
        sa.Column('to_status', sa.String(length=30), nullable=False),
        sa.Column('triggered_by', sa.String(length=20), nullable=False),
        sa.Column('is_unusual', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_status_transitions_opportunity_id'), 'status_transitions', ['opportunity_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_status_transitions_opportunity_id'), table_name='status_transitions')
    op.drop_table('status_transitions')
    op.drop_index(op.f('ix_opportunities_last_interaction_at'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_status'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_candidate_id'), table_name='opportunities')
    op.drop_table('opportunities')
