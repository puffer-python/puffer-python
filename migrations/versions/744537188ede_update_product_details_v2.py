"""update product_details_v2

Revision ID: 744537188ede
Revises: 9cef9cdb7107
Create Date: 2021-08-27 13:39:41.504246

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '744537188ede'
down_revision = '9cef9cdb7107'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_details_v2', sa.Column('manufacture', sa.Text(), nullable=True))
    # op.drop_column('product_details_v2', 'manufacturer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.add_column('product_details_v2',
    #               sa.Column('manufacturer', mysql.TEXT(charset='utf8mb4', collation='utf8mb4_0900_ai_ci'),
    #                         nullable=True))
    op.drop_column('product_details_v2', 'manufacture')
    # ### end Alembic commands ###
