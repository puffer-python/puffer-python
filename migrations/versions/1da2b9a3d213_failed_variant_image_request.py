"""empty message

Revision ID: 1da2b9a3d213
Revises: d466d79f6818
Create Date: 2021-01-12 14:26:32.887203
Create By: Minh.ND1

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1da2b9a3d213'
down_revision = 'd466d79f6818'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('failed_variant_image_request',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
                    sa.Column('request_id', type_=sa.String(40)),
                    sa.Column('status', sa.SMALLINT()),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
                    sa.Column('updated_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
                    )


def downgrade():
    op.drop_table('failed_variant_image_request')
