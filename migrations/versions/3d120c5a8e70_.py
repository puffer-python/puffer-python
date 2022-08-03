"""empty message

Revision ID: 3d120c5a8e70
Revises: d93a842923e9
Create Date: 2020-10-09 09:26:26.633485

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d120c5a8e70'
down_revision = 'b85d4beaf936'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('all_uom_ratios', type_=sa.Text))
    op.add_column('product_variants', sa.Column('all_uom_ratios', type_=sa.Text))
    op.drop_column('sellable_products', 'all_uoms')


def downgrade():
    op.drop_column('sellable_products', 'all_uom_ratios')
    op.drop_column('product_variants', 'all_uom_ratios')
    op.add_column('sellable_products',
                  sa.Column('all_uoms', type_=sa.String(255), nullable=True))

