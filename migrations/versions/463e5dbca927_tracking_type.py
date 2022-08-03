"""empty message

Revision ID: 463e5dbca927
Revises: b8e27c42e830
Create Date: 2021-09-16 16:16:18.665381

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '463e5dbca927'
down_revision = 'b8e27c42e830'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('tracking_type', sa.Boolean(), server_default='0'))


def downgrade():
    op.drop_column('sellable_products', 'tracking_type')
