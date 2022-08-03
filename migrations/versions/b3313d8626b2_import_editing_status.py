"""empty message

Revision ID: b3313d8626b2
Revises: d92cb19309a4
Create Date: 2021-12-22 18:10:05.305010

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'b3313d8626b2'
down_revision = 'd92cb19309a4'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text('''
        UPDATE misc
        SET name = 'Cập nhật trạng thái nhập liệu'
        WHERE code = 'update_editing_status';
    '''))


def downgrade():
    op.execute(text('''
        UPDATE misc
        SET name = 'Cập nhật trạng thái sản phẩm '
        WHERE code = 'update_editing_status';
    '''))
