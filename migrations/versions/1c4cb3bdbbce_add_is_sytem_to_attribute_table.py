"""empty message

Revision ID: 1c4cb3bdbbce
Revises: 3383669a0955
Create Date: 2022-02-16 21:33:36.752697

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c4cb3bdbbce'
down_revision = '3383669a0955'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attributes', sa.Column('is_system', sa.Integer(), nullable=True, default=0))


def downgrade():
    op.drop_column('attributes', 'is_system')
