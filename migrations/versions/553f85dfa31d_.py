"""empty message

Revision ID: 553f85dfa31d
Revises: 823a3f27e4bd
Create Date: 2020-09-22 10:20:30.570662

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '553f85dfa31d'
down_revision = 'e96e794d0c69'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("shipping_policy_mapping__UNIQUE_provider_id__category_id", "shipping_policy_mapping", ["provider_id", "category_id"])
    pass


def downgrade():
    op.drop_constraint("shipping_policy_mapping__UNIQUE_provider_id__category_id", "shipping_policy_mapping", "unique")
    pass
