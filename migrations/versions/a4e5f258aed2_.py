"""empty message

Revision ID: a4e5f258aed2
Revises: b18a10968dc7
Create Date: 2020-12-09 16:38:17.003278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4e5f258aed2'
down_revision = 'b18a10968dc7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('uom_name', sa.String(255)))


def downgrade():
    op.drop_column('sellable_products', 'uom_name')
