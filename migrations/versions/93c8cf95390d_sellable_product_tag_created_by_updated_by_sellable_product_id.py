"""empty message
Create Date: 2020-12-02 14:46:26.451878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import mysql

revision = '93c8cf95390d'
down_revision = '1da2b9a3d213'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'sellable_product_tags', 'sellable_product_id',
        existing_type=mysql.VARCHAR(255),
        type_=mysql.INTEGER(display_width=11, unsigned=True),
        nullable=False
    )

    op.add_column('sellable_product_tags', sa.Column('created_by', type_=sa.String(length=255), nullable=True))
    op.add_column('sellable_product_tags', sa.Column('updated_by', type_=sa.String(length=255), nullable=True))


def downgrade():
    op.alter_column(
        'sellable_product_tags', 'sellable_product_id',
        existing_type=mysql.INTEGER(display_width=11, unsigned=True),
        type_=mysql.VARCHAR(255),
        nullable=False
    )

    op.drop_column('sellable_product_tags', 'created_by')
    op.drop_column('sellable_product_tags', 'updated_by')

