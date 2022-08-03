"""Add uom name to product detail v2 table

Revision ID: fb2e1e777775
Revises: f8c79b2fb4ca
Create Date: 2022-03-08 09:55:47.179329

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fb2e1e777775'
down_revision = 'f8c79b2fb4ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_details_v2', sa.Column('uom_name', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_details_v2', 'uom_name')
    # ### end Alembic commands ###