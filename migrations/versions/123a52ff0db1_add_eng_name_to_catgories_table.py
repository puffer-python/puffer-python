"""Add eng_name to catgories table

Revision ID: 123a52ff0db1
Revises: 098ccce6f60c
Create Date: 2021-05-05 10:28:47.766719

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '123a52ff0db1'
down_revision = '098ccce6f60c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('categories', sa.Column('eng_name', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('categories', 'eng_name')
    # ### end Alembic commands ###
