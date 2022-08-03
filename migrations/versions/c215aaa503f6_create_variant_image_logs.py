"""empty message

Revision ID: c215aaa503f6
Revises: e24342f41628
Create Date: 2020-09-08 16:05:59.473438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c215aaa503f6'
down_revision = 'e24342f41628'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('variant_image_logs',
                    sa.Column('variant_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('input_url', sa.Text(), nullable=False),
                    sa.Column('result', sa.String(length=255), nullable=True),
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
                    sa.Column('updated_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
                    )


def downgrade():
    op.drop_table('variant_image_logs')
