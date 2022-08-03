"""empty message

Revision ID: 175ae877101c
Revises: 823a3f27e4bd
Create Date: 2020-09-10 15:29:52.118709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '175ae877101c'
down_revision = '823a3f27e4bd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('master_category_id', type_=sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('categories', 'master_category_id')
