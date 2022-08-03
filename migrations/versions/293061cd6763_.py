"""empty message

Revision ID: 293061cd6763
Revises: 62becc0611aa
Create Date: 2020-07-20 10:44:24.967406

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '293061cd6763'
down_revision = '62becc0611aa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attributes', sa.Column('is_float', type_=sa.Integer(), default=0))
    op.add_column('attributes', sa.Column('is_unsigned', type_=sa.Integer(), default=0))


def downgrade():
    op.drop_column('attributes', 'is_float')
    op.drop_column('attributes', 'is_unsigned')
