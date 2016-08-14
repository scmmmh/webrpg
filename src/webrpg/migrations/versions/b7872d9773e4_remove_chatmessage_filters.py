"""
##########################
Remove ChatMessage filters
##########################

Revision ID: b7872d9773e4
Revises: 98969b8ce4d2
Create Date: 2016-08-14 14:57:01.679887
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7872d9773e4'
down_revision = '98969b8ce4d2'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('chat_messages', 'filters')


def downgrade():
    op.add_column('chat_messages', sa.Column('filters', sa.Unicode(255)))
