"""
#####################
Add support for maps.
#####################

Revision ID: 9590ee34be
Revises:
Create Date: 2015-07-16 10:49:50.931272

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9590ee34be'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('maps',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('session_id', sa.Integer, sa.ForeignKey('sessions.id', name='maps_session_id_fk')),
                    sa.Column('title', sa.Unicode(255)),
                    sa.Column('map', sa.UnicodeText),
                    sa.Column('fog', sa.UnicodeText))


def downgrade():
    op.drop_table('maps')
