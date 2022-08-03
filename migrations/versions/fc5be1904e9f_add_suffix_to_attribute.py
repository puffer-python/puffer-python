"""empty message

Revision ID: fc5be1904e9f
Revises: db0725a93d87
Create Date: 2021-09-30 09:28:33.229141

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fc5be1904e9f'
down_revision = 'db0725a93d87'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attributes', sa.Column('suffix', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('attributes', 'suffix')
