"""empty message

Revision ID: ab2f48bed96c
Revises: d67048c07810
Create Date: 2020-08-27 11:10:46.490561

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ab2f48bed96c'
down_revision = 'd67048c07810'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('master_category_attribute',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
                    sa.Column('master_category_id', sa.Integer(), index=True),
                    sa.Column('attribute_id', sa.Integer(), index=True),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), ),
                    sa.Column('updated_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
                    )


def downgrade():
    op.drop_table('master_category_attribute')
