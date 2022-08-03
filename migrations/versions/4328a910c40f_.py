"""empty message

Revision ID: 4328a910c40f
Revises: 0c676d6ba6bf
Create Date: 2022-05-05 15:09:59.817459

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '4328a910c40f'
down_revision = '0c676d6ba6bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('category_index_seller_id_depth', 'categories', ['seller_id', 'depth'], unique=False)
    
