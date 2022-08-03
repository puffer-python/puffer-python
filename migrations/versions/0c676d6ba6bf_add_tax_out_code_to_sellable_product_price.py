"""empty message

Revision ID: 0c676d6ba6bf
Revises: fa7722e64c8f
Create Date: 2022-04-14 07:06:52.526079

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0c676d6ba6bf'
down_revision = 'fa7722e64c8f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_product_price', sa.Column('tax_out_code', type_=sa.String(255), nullable=True))


def downgrade():
    op.drop_column('sellable_product_price', 'tax_out_code')
