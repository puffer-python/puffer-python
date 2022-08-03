"""empty message

Revision ID: 2b95f37ff8cb
Revises: 123a52ff0db1
Create Date: 2021-04-23 14:03:52.251615

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b95f37ff8cb'
down_revision = '123a52ff0db1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('request_logs',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
                    sa.Column('request_ip', sa.String(length=15), nullable=True),
                    sa.Column('request_host', sa.String(length=255), nullable=True),
                    sa.Column('request_method', sa.String(length=15), nullable=True),
                    sa.Column('request_path', sa.Text(), nullable=True),
                    sa.Column('request_params', sa.Text(), nullable=True),
                    sa.Column('request_body', sa.Text(), nullable=True),
                    sa.Column('response_body', sa.Text(), nullable=True),
                    sa.Column('created_by', sa.String(length=255), nullable=True),
                    sa.Column('updated_by', sa.String(length=255), nullable=True),
                    sa.Column('created_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP'),
                              nullable=False),
                    sa.Column('updated_at', sa.TIMESTAMP(),
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                              nullable=False)
                    )


def downgrade():
    op.drop_table('request_logs')
