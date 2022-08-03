import re

from catalog.extensions.exceptions import BadRequestException


def validate_required(obj, message='Null Pointer Exception'):
    if obj is None:
        raise BadRequestException(message)


def validate_a_list_required(
        obj_model, list_input, field,
        apply_is_active=False,
        message='Không tồn tại hoặc đã bị vô hiệu'
):
    query = obj_model.query.filter(
        getattr(obj_model, field).in_(list_input),
    )

    if apply_is_active:
        query = query.filter(
            obj_model.is_active == 1
        )

    entity_count = query.count()
    if entity_count != len(list_input):
        raise BadRequestException(message)
