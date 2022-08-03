"""empty message

Revision ID: 6d5240ddcc3a
Revises: 28e21abb971e
Create Date: 2020-06-09 17:49:37.725301

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
from sqlalchemy.orm import sessionmaker

revision = '6d5240ddcc3a'
down_revision = '28e21abb971e'
branch_labels = None
depends_on = None

Session = sessionmaker()

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    after_update_sql = """
                    CREATE TRIGGER product_log_update
                    AFTER UPDATE
                    ON product_details
                    FOR EACH ROW
                    BEGIN
                            INSERT INTO product_logs(updated_by, sku, old_data, new_data)
                            VALUES(new.updated_by, new.sku, old.data, new.data);
                    END;
                    """

    after_insert_sql = """
                        CREATE TRIGGER product_log_insert
                        AFTER INSERT
                        ON product_details
                        FOR EACH ROW
                        BEGIN
                                INSERT INTO product_logs(updated_by, sku, old_data, new_data)
                                VALUES(new.updated_by, new.sku, NULL, new.data);
                        END;
                        """
    sesssion.execute(after_insert_sql)
    sesssion.execute(after_update_sql)
    sesssion.commit()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    drop_update_trigger_sql = """Drop trigger product_log_update;"""
    drop_insert_trigger_sql = """Drop trigger product_log_update;"""
    sesssion.execute(drop_insert_trigger_sql)
    sesssion.execute(drop_update_trigger_sql)
    sesssion.commit()
    # ### end Alembic commands ###
