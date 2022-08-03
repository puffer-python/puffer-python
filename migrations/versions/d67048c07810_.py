"""empty message

Revision ID: d67048c07810
Revises: 45a9328df542
Create Date: 2020-08-07 16:04:38.668985

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd67048c07810'
down_revision = '45a9328df542'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('unique_sellable_product_id_terminal_group_code',
                                'sellable_product_terminal_group',
                                ['sellable_product_id', 'terminal_group_code'])


def downgrade():
    op.drop_constraint(
        'unique_sellable_product_id_terminal_group_code',
        'sellable_product_terminal_group',
        type_='unique'
    )
