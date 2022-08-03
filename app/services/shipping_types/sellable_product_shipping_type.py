from flask_login import current_user

from catalog import models


class SellableProductShippingTypeService:
    @staticmethod
    def create(sellable_product_id, shipping_type_id, auto_commit=True):
        entity = models.SellableProductShippingType(
            sellable_product_id=sellable_product_id,
            shipping_type_id=shipping_type_id,
            created_by=current_user.email if hasattr(current_user, 'email') else ''
        )

        models.db.session.add(entity)
        if auto_commit:
            models.db.session.commit()

        return entity

    @staticmethod
    def delete(sellable_product_id, auto_commit=True):
        models.SellableProductShippingType.query.filter(
            models.SellableProductShippingType.sellable_product_id == sellable_product_id
        ).delete(synchronize_session='fetch')

        if auto_commit:
            models.db.session.commit()
