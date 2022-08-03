def get_default(value):
    return value or ''


def get_variant_attribute_value(variant_attribute):
    attribute = variant_attribute.get('attribute')
    value_type = attribute.get('value_type')
    value = variant_attribute.get('value')
    if value_type in ('text', 'number'):
        return value
    options = attribute.get('options') or []
    if options:
        values = []
        for o in options:
            values.append(f'{o.get("value")} {o.get("unit_code")}'.strip())
        return str.join(', ', values)
