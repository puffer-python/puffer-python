from catalog.models import db, TimestampMixin


class SellableProductTerminalGroup(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_terminal_group'

    sellable_product_id = db.Column(
        db.Integer,
        db.ForeignKey('sellable_products.id'),
        nullable=False
    )
    terminal_group_code = db.Column(
        db.String(255),
        db.ForeignKey('terminal_groups.code'),
        nullable=False
    )
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
