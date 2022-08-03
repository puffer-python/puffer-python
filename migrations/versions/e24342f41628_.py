"""empty message

Revision ID: d67048c07810
Revises: 45a9328df542
Create Date: 2020-08-07 16:04:38.668985

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
# revision identifiers, used by Alembic.
revision = 'e24342f41628'
down_revision = 'ab2f48bed96c'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    sesssion = Session(bind=bind)
    drop_update_trigger_sql = """Drop trigger if exists product_log_update;"""
    sesssion.execute(drop_update_trigger_sql)

    after_update_sql = """
                        CREATE TRIGGER product_log_update
                        AFTER UPDATE
                        ON product_details
                        FOR EACH ROW
                        BEGIN
                            IF (new.data != old.data)
                            THEN
                                INSERT INTO product_logs(updated_by, sku, old_data, new_data)
                                VALUES(new.updated_by, new.sku, old.data, new.data);
                            END IF;
                        END;
                        """

    sesssion.execute(after_update_sql)

    sesssion.commit()




def downgrade():
    pass
