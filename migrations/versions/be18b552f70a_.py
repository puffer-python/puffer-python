"""empty message

Revision ID: be18b552f70a
Revises: 577775147533
Create Date: 2020-06-09 09:17:34.387016

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'be18b552f70a'
down_revision = 'e1903625ca83'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('variant_images_product_variant_id_index', 'variant_images', ['product_variant_id'])


def downgrade():
    op.drop_index('variant_images_product_variant_id_index')
