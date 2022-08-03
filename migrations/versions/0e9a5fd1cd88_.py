"""empty message

Revision ID: 0e9a5fd1cd88
Revises: c3d18b3dec07
Create Date: 2021-06-06 16:07:53.365395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

revision = '0e9a5fd1cd88'
down_revision = 'c3d18b3dec07'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            """
                update misc set config = :config where `type` = 'import_type' and `code` = 'update_editing_status'
            """
        ), {
            "config": '{"version":1}'
        }
    )
    conn.execute(
        text(
            """
                update misc set config = :config where `type`='import_type' and `code` = 'update_product'
            """
        ), {
            "config": '{"version":3}'
        }
    )
    conn.execute(
        text(
            """
                update misc set config = :config where `type`='import_type' and `code` = 'update_attribute_product'
            """
        ), {
            "config": '{"version":3}'
        }
    )
    conn.execute(
        text(
            """
                update misc set config = :config where `type`='import_type' and `code` = 'update_images_skus'
            """
        ), {
            "config": '{"version":3}'
        }
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            """
                update misc set config = null where `type`='import_type' and `code` = 'update_product'
            """
        )
    )
    conn.execute(
        text(
            """
                update misc set config = null where `type`='import_type' and `code` = 'update_attribute_product'
            """
        )
    )
    conn.execute(
        text(
            """
                update misc set config = null where `type`='import_type' and `code` = 'update_images_skus'
            """
        )
    )
    conn.execute(
        text(
            """
                update misc set config = null where `type` = 'import_type' and `code` = 'update_editing_status'
            """
        )
    )
