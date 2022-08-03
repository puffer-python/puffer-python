"""empty message

Revision ID: 1b9cfe911c01
Revises: 3d120c5a8e70
Create Date: 2020-11-25 17:25:04.831223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b9cfe911c01'
down_revision = '3d120c5a8e70'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('variant_images', sa.Column('created_by', type_=sa.String(length=255), nullable=True))
    op.add_column('variant_images', sa.Column('updated_by', type_=sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('variant_images', 'created_by')
    op.drop_column('variant_images', 'updated_by')
