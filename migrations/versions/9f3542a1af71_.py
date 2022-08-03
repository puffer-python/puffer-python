"""empty message

Revision ID: 9f3542a1af71
Revises: 1b9cfe911c01
Create Date: 2020-11-24 14:24:57.700204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f3542a1af71'
down_revision = 'da168e9f789d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attribute_options', sa.Column('seller_id', sa.Integer()))
    op.add_column('attribute_options', sa.Column('code', sa.String(30)))


def downgrade():
    op.drop_column('attribute_options', 'seller_id')
    op.drop_column('attribute_options', 'code')
