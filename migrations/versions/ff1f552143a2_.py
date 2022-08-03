"""empty message

Revision ID: ff1f552143a2
Revises: 9f3542a1af71
Create Date: 2020-12-15 11:46:36.480823

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ff1f552143a2'
down_revision = '9f3542a1af71'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('products', 'unit_id', type_=sa.Integer(), nullable=True)


def downgrade():
    op.alter_column('products', 'unit_id', type_=sa.Integer(), nullable=False)
