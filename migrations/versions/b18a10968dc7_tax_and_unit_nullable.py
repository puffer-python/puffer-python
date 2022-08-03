"""empty message

Revision ID: b18a10968dc7
Revises: 1b9cfe911c01
Create Date: 2020-12-01 15:14:25.304902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b18a10968dc7'
down_revision = '1b9cfe911c01'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('categories', 'tax_in_code', type_=sa.String(10), nullable=True)
    op.alter_column('categories', 'tax_out_code', type_=sa.String(10), nullable=True)


def downgrade():
    pass
