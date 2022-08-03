"""empty message

Revision ID: 971c614677d0
Revises: ffb7d4a25a17
Create Date: 2021-12-15 16:29:36.397252

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '971c614677d0'
down_revision = 'ffb7d4a25a17'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('attribute_options', sa.Column('priority', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('attribute_options', 'priority')
    # ### end Alembic commands ###
