"""empty message

Revision ID: 4f4cc7e3f543
Revises: 59dcd9aac874
Create Date: 2020-06-17 12:02:10.488033

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4f4cc7e3f543'
down_revision = '59dcd9aac874'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellers', sa.Column('created_at', type_=sa.TIMESTAMP()))
    op.add_column('sellers', sa.Column('updated_at', type_=sa.TIMESTAMP()))


def downgrade():
    op.drop_column('sellers', 'created_at')
    op.drop_column('sellers', 'updated_at')
