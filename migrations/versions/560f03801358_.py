"""empty message

Revision ID: 560f03801358
Revises: 577775147533
Create Date: 2020-06-09 13:58:57.182772

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '560f03801358'
down_revision = '577775147533'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('variant_attribute', sa.Column('unit_id', type_=sa.Integer()))
    op.create_index('variant_attribute_unit_id_index', 'variant_attribute', ['unit_id'])


def downgrade():
    op.drop_column('variant_attribute', 'unit_id')
