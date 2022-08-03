"""empty message

Revision ID: 1ae38a9c207a
Revises: 97884ae7c732
Create Date: 2021-07-22 19:15:04.280687

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = '1ae38a9c207a'
down_revision = '97884ae7c732'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            """
                update misc set config = :config where `type` = 'import_type' and `code` = 'create_product'
            """
        ), {
            "config": '{"version":1}'
        }
    )
    conn.execute(
        text(
            """
                update misc set config = :config where `type`='import_type' and `code` = 'create_product_basic_info'
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
                update misc set config = null where `type`='import_type' and `code` = 'create_product'
            """
        )
    )
    conn.execute(
        text(
            """
                update misc set config = null where `type`='import_type' and `code` = 'create_product_basic_info'
            """
        )
    )
