"""empty message

Revision ID: 5b84e26fadeb
Revises: 93c8cf95390d
Create Date: 2021-03-04 14:19:55.689457
Create By: Dung.BV
Description: Convert attribute_options to utf8mb4_bin

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = '5b84e26fadeb'
down_revision = '93c8cf95390d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        text('ALTER TABLE attribute_options CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin')
    )


def downgrade():
    pass
