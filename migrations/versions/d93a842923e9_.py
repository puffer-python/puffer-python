"""empty message

Revision ID: d93a842923e9
Revises: 553f85dfa31d
Create Date: 2020-10-01 09:42:30.543680

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd93a842923e9'
down_revision = '553f85dfa31d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('master_categories', sa.Column('name_ascii', type_=sa.String(255)))


def downgrade():
    op.drop_column('master_categories', 'name_ascii')
