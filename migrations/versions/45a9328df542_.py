"""empty message

Revision ID: 45a9328df542
Revises: e04b8a0bc03b
Create Date: 2020-08-03 14:23:04.244170

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func, exists, and_

from catalog import models as m


# revision identifiers, used by Alembic.
revision = '45a9328df542'
down_revision = 'e04b8a0bc03b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('shipping_policy', sa.Column('name', type_=sa.String(255)))

    # seed shipping type data
    for name, code in [
        ('Giao toàn quốc', 'all'),
        ('Giao hàng cồng kềnh', 'bulky'),
        ('Giao hàng gần', 'near')
    ]:
        existed = m.db.session.query(
            exists().where(and_(
                m.Misc.code == code,
                m.Misc.type == 'shipping_type'
            ))
        ).scalar()
        if not existed:
            misc = m.Misc()
            misc.name = name
            misc.code = code
            misc.type = 'shipping_type'
            m.db.session.add(misc)

    m.db.session.commit()


def downgrade():
    op.drop_column('shipping_policy', 'name')
