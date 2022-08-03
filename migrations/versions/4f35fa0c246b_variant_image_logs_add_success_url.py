"""empty message

Revision ID: 4f35fa0c246b
Revises: ff1f552143a2
Create Date: 2020-12-28 16:52:30.010693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f35fa0c246b'
down_revision = 'ff1f552143a2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('variant_image_logs', sa.Column('success_url', type_=sa.Text(), nullable=True))


def downgrade():
    pass
