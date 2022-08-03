"""empty message

Revision ID: e1903625ca83
Revises: a0a0e532bbca
Create Date: 2020-06-04 14:56:57.333031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1903625ca83'
down_revision = 'a0a0e532bbca'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('iam_users', sa.Column('seller_ids', type_=sa.String(255)))


def downgrade():
    op.drop_column('iam_users', 'seller_ids')
