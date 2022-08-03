"""empty message

Revision ID: 8ceee93ceb53
Revises: 293061cd6763
Create Date: 2020-07-22 10:53:51.607500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ceee93ceb53'
down_revision = '293061cd6763'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('terminal_groups',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('code', sa.String(255)),
                    sa.Column('name', sa.String(255)),
                    sa.Column('type', sa.String(255)),
                    sa.Column('seller_id', sa.Integer()),
                    sa.Column('is_active', sa.Boolean()),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    )
    op.create_table('terminal_group_terminal',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('terminal_code', sa.String(255)),
                    sa.Column('terminal_group_code', sa.String(255)),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    )


def downgrade():
    op.drop_table('terminal_groups')
    op.drop_table('terminal_group_terminal')
