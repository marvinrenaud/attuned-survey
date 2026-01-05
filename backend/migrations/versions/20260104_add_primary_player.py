"""add primary_player_id to activity_history

Revision ID: 20260104_add_primary_player
Revises: 
Create Date: 2026-01-04 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260104_add_primary_player'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if column exists first to be safe (sqlite/postgres differences handled via op)
    # Using simple add_column for now
    with op.batch_alter_table('user_activity_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('primary_player_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_activity_history_primary_player_id'), ['primary_player_id'], unique=False)


def downgrade():
    with op.batch_alter_table('user_activity_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_activity_history_primary_player_id'))
        batch_op.drop_column('primary_player_id')
