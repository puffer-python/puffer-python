"""empty message

Revision ID: e96e794d0c69
Revises: 175ae877101c
Create Date: 2020-09-22 15:22:26.034723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import table
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

revision = 'e96e794d0c69'
down_revision = '175ae877101c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('all_uoms', type_=sa.String(255), nullable=True))
    op.add_column('sellable_products', sa.Column('uom_ratio', type_=sa.Float(), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)
    set_default_values = """UPDATE sellable_products
                            SET all_uoms = sellable_products.id,
                                uom_ratio = 1.0;"""

    session.execute(set_default_values)
    session.commit()


def downgrade():
    op.drop_column('sellable_products', 'all_uoms')
    op.drop_column('sellable_products', 'uom_ratio')

