"""Add players, game_settings, and current_turn_state to sessions table

Revision ID: add_session_json_fields
Revises: previous_revision
Create Date: 2025-12-10 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_session_json_fields'
down_revision = '005_add_session_mvp_fields'  # Assuming this is the previous one based on file content
branch_labels = None
depends_on = None


def upgrade():
    # Add new JSONB columns
    op.add_column('sessions', sa.Column('players', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('game_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('current_turn_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('sessions', 'current_turn_state')
    op.drop_column('sessions', 'game_settings')
    op.drop_column('sessions', 'players')
