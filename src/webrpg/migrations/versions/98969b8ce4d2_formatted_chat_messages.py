"""
################################################
Add field for explicitly formatted chat messages
################################################

Revision ID: 98969b8ce4d2
Revises:
Create Date: 2016-08-14 13:26:43.260884
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '98969b8ce4d2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_messages', sa.Column('formatted', sa.UnicodeText()))


def downgrade():
    op.drop_column('chat_messages', 'formatted')
