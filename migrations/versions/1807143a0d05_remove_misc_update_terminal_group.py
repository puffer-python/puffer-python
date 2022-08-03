"""empty message

Revision ID: 1807143a0d05
Revises: b339981631a9
Create Date: 2022-02-14 13:31:57.861308

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = '1807143a0d05'
down_revision = 'b339981631a9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    sql_delete = """DELETE FROM misc WHERE code = 'update_terminal_groups';"""
    sesssion.execute(sql_delete)
    sesssion.commit()


def downgrade():
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    sql_insert = """
        INSERT INTO misc (`name`, `type`, `code`) 
        VALUES 
        ('Cập nhật nhóm điểm bán', 'import_type', 'update_terminal_groups')
    """
    sesssion.execute(sql_insert)
    sesssion.commit()
