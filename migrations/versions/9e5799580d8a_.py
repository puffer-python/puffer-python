"""empty message

Revision ID: 9e5799580d8a
Revises: 560f03801358
Create Date: 2020-06-12 11:13:26.556174

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9e5799580d8a'
down_revision = '560f03801358'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('providers', sa.Column('logo', type_=sa.String(500)))
    op.add_column('providers', sa.Column('slogan', type_=sa.String(255)))


def downgrade():
    op.drop_column('providers', 'logo')
    op.drop_column('providers', 'slogan')
