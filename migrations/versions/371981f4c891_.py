"""empty message

Revision ID: 371981f4c891
Revises: 87dd8f119e34
Create Date: 2020-07-28 13:55:38.715019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '371981f4c891'
down_revision = '87dd8f119e34'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sellable_product_terminal_group',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('sellable_product_id', sa.Integer()),
                    sa.Column('terminal_group_code', sa.String(255), nullable=False),
                    sa.Column('created_by', sa.String(255)),
                    sa.Column('updated_by', sa.String(255)),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
                    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index('sellable_products_terminal_group_code_index', 'sellable_product_terminal_group', ['terminal_group_code'])
    op.create_index('sellable_products_terminal_sellable_product_id_index', 'sellable_product_terminal_group', ['sellable_product_id'])


def downgrade():
    op.drop_table('sellable_product_terminal_group')
