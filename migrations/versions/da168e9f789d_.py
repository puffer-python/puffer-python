"""empty message

Revision ID: da168e9f789d
Revises: 3d120c5a8e70
Create Date: 2020-11-11 09:45:48.056565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da168e9f789d'
down_revision = '632d18aae20a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('uom_code', type_=sa.Text))
    op.drop_column('sellable_products', 'all_uom_ratios')


def downgrade():
    op.drop_column('sellable_products', 'uom_code')
    op.drop_column('sellable_products', 'all_uom_ratios')
    op.add_column('sellable_products', sa.Column('all_uom_ratios', type_=sa.Text))
