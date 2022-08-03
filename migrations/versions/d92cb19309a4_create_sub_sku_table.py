"""create_sub_sku_table

Revision ID: d92cb19309a4
Revises: f9fa2fdad980
Create Date: 2021-11-23 14:26:39.889568

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd92cb19309a4'
down_revision = 'f9fa2fdad980'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sellable_product_sub_sku',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sellable_product_id', sa.Integer, nullable=False, index=True),
        sa.Column('sub_sku', sa.String(255), nullable=False, index=True),
        sa.Column('is_active', sa.Integer, default=1),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    )


def downgrade():
    op.drop_table('sellable_product_sub_sku')
