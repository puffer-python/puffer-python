"""empty message

Revision ID: 3383669a0955
Revises: 225d722da422
Create Date: 2022-01-25 11:42:47.115947

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3383669a0955'
down_revision = '225d722da422'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sellable_product_price',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
                    sa.Column('sellable_product_id', sa.Integer(), nullable=False),
                    sa.Column('selling_status', sa.Integer(), nullable=False, default=1),
                    sa.Column('selling_price', sa.Integer(), nullable=True),
                    sa.Column('terminal_group_ids', sa.String(length=255), nullable=True,
                              comment="JSON ARRAY of the terminal group ids"),
                    sa.Column('created_by', sa.String(length=255), nullable=True),
                    sa.Column('updated_by', sa.String(length=255), nullable=True),
                    sa.Column('created_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP'),
                              nullable=False),
                    sa.Column('updated_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                              nullable=False)
                    )


def downgrade():
    op.drop_table('sellable_product_price')
