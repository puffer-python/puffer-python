"""empty message

Revision ID: cbb91685c99b
Revises: 2b95f37ff8cb
Create Date: 2021-05-24 20:40:25.495922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import mysql

revision = 'cbb91685c99b'
down_revision = '2b95f37ff8cb'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('request_logs', 'response_body',
                    nullable=True, type_=mysql.LONGTEXT())


def downgrade():
    pass
