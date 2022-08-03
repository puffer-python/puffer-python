"""empty message

Revision ID: 3d6f9e838de7
Revises: d93a842923e9
Create Date: 2020-10-19 13:15:21.347477

"""
from alembic import op

from catalog.models import db
from catalog.models.sellable_product import SellableProduct
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d6f9e838de7'
down_revision = 'd93a842923e9'
branch_labels = None
depends_on = None


def upgrade():
    sql = sa.update(SellableProduct).where(
        SellableProduct.expiry_tracking == 0
    ).values(days_before_exp_lock=None, expiration_type=None)

    db.session.execute(sql)
    db.session.commit()


def downgrade():
    pass
