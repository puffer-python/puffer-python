"""empty message
Create By: Dung.BV
Create Date: 2021-07-23 15:59:59.039019

"""
from alembic import op
import sqlalchemy as sa
from catalog.models import db

# revision identifiers, used by Alembic.
revision = 'f99b52ecbca7'
down_revision = '05c139f98888'
branch_labels = None
depends_on = None


def upgrade():
    query = """
                    SELECT COUNT(*) as count
                    FROM `attributes` a
                    WHERE a.code = :code
                """
    results = db.engine.execute(sa.text(query), {'code': 'manufacture'})
    total = 0
    for r in results:
        total = r['count']
    if total == 0:
        inser_query = """
            INSERT INTO attributes (code, name,  display_name, description, value_type) 
            VALUE (:code, :name, :display_name, :description, :value_type)
        """
        db.engine.execute(sa.text(inser_query), {
            'code': 'manufacture',
            'name': 'Nhà sản xuất',
            'display_name': 'Nhà sản xuất',
            'description': 'The manufacture of the products. Type of this attribute is selection',
            'value_type': 'selection'
        })


def downgrade():
    pass
