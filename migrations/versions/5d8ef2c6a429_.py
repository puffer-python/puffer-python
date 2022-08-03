"""empty message

Revision ID: 5d8ef2c6a429
Revises: 4f4cc7e3f543
Create Date: 2020-06-17 12:02:10.488033

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5d8ef2c6a429'
down_revision = '4f4cc7e3f543'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellers', sa.Column('slogan', type_=sa.Text()))


def downgrade():
    op.drop_column('sellers', 'slogan')
