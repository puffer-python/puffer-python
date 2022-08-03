from flask_login import current_user

from catalog import models


class CategoryShippingTypeService:
    @staticmethod
    def create(category_id, shipping_type_id, auto_commit=True):
        entity = models.CategoryShippingType(
            category_id=category_id,
            shipping_type_id=shipping_type_id,
            created_by=current_user.email,
            updated_by=current_user.email
        )

        models.db.session.add(entity)
        if auto_commit:
            models.db.session.commit()

        return entity

    @staticmethod
    def delete(category_id, auto_commit=True):
        models.CategoryShippingType.query.filter(
            models.CategoryShippingType.category_id == category_id
        ).delete(synchronize_session='fetch')

        if auto_commit:
            models.db.session.commit()

