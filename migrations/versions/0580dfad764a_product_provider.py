"""empty message

Revision ID: 0580dfad764a
Revises: e5c1b70eeffe
Create Date: 2021-08-27 17:18:30.521950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0580dfad764a'
down_revision = 'e5c1b70eeffe'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('provider_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('products', 'provider_id')
