"""empty message

Revision ID: 632d18aae20a
Revises: 3d120c5a8e70
Create Date: 2020-11-13 17:26:49.662189

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = '632d18aae20a'
down_revision = 'a4e5f258aed2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellable_products', sa.Column('seller_sku', type_=sa.String(255)))
    op.create_index('sellable_products_seller_sku', 'sellable_products',
                    ['seller_sku'])

    sql = "UPDATE sellable_products SET seller_sku = sku"
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sql)
    session.commit()


def downgrade():
    op.drop_column('sellable_products', 'seller_sku')
