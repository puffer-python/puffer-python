"""empty message

Revision ID: 5720c231b0ed
Revises: fc5be1904e9f
Create Date: 2021-11-18 12:58:22.290256

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5720c231b0ed'
down_revision = 'fc5be1904e9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_details_v2', sa.Column('barcodes', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_details_v2', 'barcodes')
    # ### end Alembic commands ###
