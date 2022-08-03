"""empty message

Revision ID: dad50b349ddc
Revises: 85cf04be53d2
Create Date: 2021-06-21 15:45:41.842405

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = 'dad50b349ddc'
down_revision = '85cf04be53d2'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            """
                update misc set config = :config where `type`='import_type' and `code` = 'update_terminal_groups'
            """
        ), {
            "config": '{"version":1}'
        }
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            """
                update misc set config = null where `type`='import_type' and `code` = 'update_terminal_groups'
            """
        )
    )
