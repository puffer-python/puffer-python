"""empty message

Revision ID: 4c12ffae73c3
Revises: 2b95f37ff8cb
Create Date: 2021-05-25 20:45:45.569800

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import mysql

revision = '4c12ffae73c3'
down_revision = 'cbb91685c99b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('units', 'name', type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255), nullable=False)
    op.alter_column('units', 'code', type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255))


def downgrade():
    op.alter_column('units', 'name', type_=mysql.VARCHAR(collation='utf8mb4_bin', length=255), nullable=False)
    op.alter_column('units', 'code', type_=mysql.VARCHAR(collation='utf8mb4_bin', length=255))
