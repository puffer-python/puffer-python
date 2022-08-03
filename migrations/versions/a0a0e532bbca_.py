"""empty message

Revision ID: a0a0e532bbca
Revises: 0f9f198cc9e8
Create Date: 2020-05-25 11:44:38.200589

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0a0e532bbca'
down_revision = '0f9f198cc9e8'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('products', 'name', type_=sa.String(500))
    op.alter_column('products', 'display_name', type_=sa.String(500))
    op.alter_column('products', 'short_name', type_=sa.String(500))
    op.alter_column('products', 'spu', type_=sa.String(10))
    op.alter_column('products', 'created_by', type_=sa.String(255))
    op.alter_column('products', 'updated_by', type_=sa.String(255))
    op.alter_column('sellable_product_bundles', 'created_by', type_=sa.String(255))


def downgrade():
    op.alter_column('products', 'name', type_=sa.String(255))
    op.alter_column('products', 'display_name', type_=sa.String(255))
    op.alter_column('products', 'short_name', type_=sa.String(255))
    op.alter_column('products', 'spu', type_=sa.Integer())
    op.alter_column('products', 'created_by', type_=sa.Integer())
    op.alter_column('products', 'updated_by', type_=sa.Integer())
    op.alter_column('sellable_product_bundles', 'created_by', type_=sa.Integer())
