"""empty message

Revision ID: ffb7d4a25a17
Revises: 5720c231b0ed
Create Date: 2021-11-17 20:39:21.564117

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = 'ffb7d4a25a17'
down_revision = '5720c231b0ed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    sesssion.execute(
        text(
            """
            INSERT INTO misc (`name`, `type`, `code`, `config`) 
            VALUES 
            ('Cập nhật thông tin SEO', 'import_type', 'update_seo_info', :config)
            """
        ), {
            "config": '{"version":1}'
        }
    )
    sesssion.commit()


def downgrade():
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    update_misc_sql = """
                        DELETE FROM misc WHERE `type` = 'import_type' AND `code` = 'update_seo_info'
                        """
    sesssion.execute(update_misc_sql)
    sesssion.commit()
