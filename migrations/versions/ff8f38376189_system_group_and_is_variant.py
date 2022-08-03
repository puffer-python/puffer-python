"""empty message

Revision ID: ff8f38376189
Revises: c886d6d67f29
Create Date: 2021-03-23 11:31:24.320582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = 'ff8f38376189'
down_revision = 'c886d6d67f29'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text('''
        UPDATE attribute_groups
        SET system_group = 0
        WHERE system_group is NULL;
    '''))

    op.execute(text('''
        UPDATE attribute_group_attribute
        SET is_variation = 0
        WHERE is_variation is NULL;
    '''))

    op.alter_column('attribute_groups', 'system_group', server_default=sa.schema.DefaultClause("0"))
    op.alter_column('attribute_group_attribute', 'is_variation', server_default=sa.schema.DefaultClause("0"))


def downgrade():
    pass
