"""empty message

Revision ID: 906ca12c6715
Revises: e1903625ca83
Create Date: 2020-06-08 15:49:57.164032

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '906ca12c6715'
down_revision = 'be18b552f70a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('sellable_products_product_type_index', 'sellable_products', ['product_type'])
    op.create_index('sellable_products_objective_index', 'sellable_products', ['objective'])
    op.create_index('sellable_products_editing_status_code_index', 'sellable_products', ['editing_status_code'])
    op.create_index('sellable_products_selling_status_code_index', 'sellable_products', ['selling_status_code'])
    op.create_index('sellable_products_seller_id_index', 'sellable_products', ['seller_id'])


def downgrade():
    op.drop_index('sellable_products_product_type_index', 'sellable_products')
    op.drop_index('sellable_products_objective_index', 'sellable_products')
    op.drop_index('sellable_products_editing_status_code_index', 'sellable_products')
    op.drop_index('sellable_products_selling_status_code_index', 'sellable_products')
    op.drop_index('sellable_products_seller_id_index', 'sellable_products')
