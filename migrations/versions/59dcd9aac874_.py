"""empty message

Revision ID: 59dcd9aac874
Revises: 6d5240ddcc3a
Create Date: 2020-06-17 11:39:08.805482

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '59dcd9aac874'
down_revision = '6d5240ddcc3a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sellers', sa.Column('english_name', type_=sa.String(500)))
    op.add_column('sellers', sa.Column('enterprise_code', type_=sa.String(255)))
    op.add_column('sellers', sa.Column('tax_number', type_=sa.String(255)))
    op.add_column('sellers', sa.Column('founding_date', type_=sa.String(255)))
    op.add_column('sellers', sa.Column('address', type_=sa.String(255)))
    op.add_column('sellers', sa.Column('contract_no', type_=sa.String(255)))
    op.add_column('sellers', sa.Column('extra', type_=sa.Text()))


def downgrade():
    op.drop_column('sellers', 'english_name')
    op.drop_column('sellers', 'enterprise_code')
    op.drop_column('sellers', 'tax_number')
    op.drop_column('sellers', 'founding_date')
    op.drop_column('sellers', 'address')
    op.drop_column('sellers', 'contract_no')
    op.drop_column('sellers', 'extra')
