"""empty message

Revision ID: 225d722da422
Revises: f7ba81939ad6
Create Date: 2022-01-24 23:35:28.079976

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '225d722da422'
down_revision = 'f7ba81939ad6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attribute_sets', sa.Column('is_default',
                                              type_=sa.Integer(), default=1, nullable=True
                                              ))


def downgrade():
    op.drop_column('attribute_sets', 'is_default')
