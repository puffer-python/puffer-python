"""empty message

Revision ID: 85cf04be53d2
Revises: 0e9a5fd1cd88
Create Date: 2021-05-30 17:22:26.919816

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '85cf04be53d2'
down_revision = '0e9a5fd1cd88'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products',
                  sa.Column('need_convert_qty', mysql.TINYINT(), nullable=False,
                            comment='Can chuyen doi so luong sang so luong cua don vi tinh base', server_default='0'))


def downgrade():
    op.drop_column('sellable_products', 'need_convert_qty')
