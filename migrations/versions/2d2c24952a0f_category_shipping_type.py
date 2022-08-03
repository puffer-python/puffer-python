"""empty message

Revision ID: 2d2c24952a0f
Revises: 4ced24dfa533
Create Date: 2021-04-05 15:23:12.754150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d2c24952a0f'
down_revision = '19b3d9857ae8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'category_shipping_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column('category_id', sa.Integer(), nullable=False, index=True),
        sa.Column('shipping_type_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                  nullable=False)
    )


def downgrade():
    op.drop_table('category_shipping_type')
