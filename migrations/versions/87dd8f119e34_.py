"""empty message

Revision ID: 87dd8f119e34
Revises: 8ceee93ceb53
Create Date: 2020-07-27 17:18:31.186215

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87dd8f119e34'
down_revision = '8ceee93ceb53'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('seller_terminal_groups',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('seller_id', sa.Integer()),
                    sa.Column('terminal_group_id', sa.Integer()),
                    sa.Column('is_requested_approval', sa.Boolean()),
                    sa.Column('is_owner', sa.Boolean()),
                    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
                    )


def downgrade():
    op.drop_table('seller_terminal_groups')
