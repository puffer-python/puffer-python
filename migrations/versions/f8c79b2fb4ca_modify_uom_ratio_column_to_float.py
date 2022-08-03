"""modify_uom_ratio_column_to_float

Revision ID: f8c79b2fb4ca
Revises: 1c4cb3bdbbce
Create Date: 2022-03-04 16:32:31.713086

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f8c79b2fb4ca'
down_revision = '1c4cb3bdbbce'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('sellable_products', 'uom_ratio', type_=sa.Float(10, 6), nullable=True)


def downgrade():
    op.alter_column('sellable_products', 'uom_ratio', type_=sa.String(255), nullable=True)
