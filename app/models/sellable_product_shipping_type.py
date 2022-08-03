from catalog.models import db, TimestampMixin


class SellableProductShippingType(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_shipping_type'

    sellable_product_id = db.Column(
        db.Integer,
        db.ForeignKey('sellable_products.id'),
        nullable=False
    )
    shipping_type_id = db.Column(
        db.Integer,
        db.ForeignKey('shipping_types.id'),
        nullable=False
    )

    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
    created_from = db.Column(db.String(255))
