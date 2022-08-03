"""empty message

Revision ID: 823a3f27e4bd
Revises: c215aaa503f6
Create Date: 2020-09-18 11:57:28.427864

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '823a3f27e4bd'
down_revision = 'c215aaa503f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('variant_image_logs', sa.Column('request_id', type_=sa.String(40)))


def downgrade():
    op.drop_column('variant_image_logs', 'request_id')
