"""empty message

Revision ID: b85d4beaf936
Revises: 3d6f9e838de7
Create Date: 2020-10-06 13:54:53.343469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b85d4beaf936'
down_revision = '3d6f9e838de7'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('variant_image_logs', 'input_url',
                    nullable=True, type_=sa.Text())


def downgrade():
    pass

