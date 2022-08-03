"""empty message

Revision ID: d466d79f6818
Revises: ff1f552143a2
Create Date: 2020-12-17 10:47:59.026402

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd466d79f6818'
down_revision = '4f35fa0c246b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('categories', 'updated_at', type_=sa.TIMESTAMP(),
                    server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    op.alter_column('master_categories', 'updated_at', type_=sa.TIMESTAMP(),
                    server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))


def downgrade():
    pass
