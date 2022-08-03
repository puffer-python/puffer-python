"""empty message

Revision ID: 098ccce6f60c
Revises: 2d2c24952a0f
Create Date: 2021-04-27 17:27:36.041436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session

revision = '098ccce6f60c'
down_revision = '2d2c24952a0f'
branch_labels = None
depends_on = None


def upgrade():
    add_new_status_sql = """
              INSERT INTO editing_status (`name`, `code`, `config`, `can_moved_status`) 
              VALUE ('Tạm ẩn hiển thị', 'suspend', '{"color": "purple"}', 'draft,pending_approval,active,inactive,reject,processing'); 
                 """;
    update_can_moved_to_sql = "UPDATE editing_status SET can_moved_status = CONCAT(can_moved_status,',suspend') WHERE code != 'suspend';"
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    sesssion.execute(add_new_status_sql)
    sesssion.execute(update_can_moved_to_sql)
    sesssion.commit()

def downgrade():
    update_can_moved_to_sql = """
                UPDATE editing_status SET can_moved_status = REPLACE(can_moved_status,',suspend', '') WHERE code != 'suspend';
                    """
    remove_suspend_status_sql = "DELETE FROM editing_status WHERE code = 'suspend'; "
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    sesssion.execute(update_can_moved_to_sql)
    sesssion.execute(remove_suspend_status_sql)
    sesssion.commit()