"""empty message

Revision ID: 577775147533
Revises: 906ca12c6715
Create Date: 2020-06-08 15:55:58.440026

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '577775147533'
down_revision = '906ca12c6715'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('categories_seller_id_index', 'categories', ['seller_id'])


def downgrade():
    op.drop_index('categories_seller_id_index', 'categories')
