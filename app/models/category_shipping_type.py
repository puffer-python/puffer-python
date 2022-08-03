from catalog.models import db, TimestampMixin


class CategoryShippingType(db.Model, TimestampMixin):
    __tablename__ = 'category_shipping_type'

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id'),
        nullable=False
    )
    shipping_type_id = db.Column(
        db.Integer,
        db.ForeignKey('shipping_types.id'),
        nullable=False
    )
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
