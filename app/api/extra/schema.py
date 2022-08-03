# coding=utf-8

from marshmallow import Schema as OriginSchema, fields as origin_fields

from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api.taxes import schema as tax_schema


class Misc(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()


class EditingStatus(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    config = fields.String()
    can_moved_status = fields.String()
    state_id = fields.Integer()


class Unit(Schema):
    id = fields.Integer()
    code = fields.String()
    name = fields.String()


class SellingStatus(Misc):
    config = fields.String()


class ImportStatus(Misc):
    config = fields.String()


class Extra(Schema):
    selling_status = fields.Nested(SellingStatus(many=True))
    editing_status = fields.Nested(EditingStatus(many=True))
    product_types = fields.Nested(Misc(many=True))
    import_types = fields.Nested(Misc(many=True))
    import_status = fields.Nested(ImportStatus(many=True))
    units = fields.Nested(Unit(many=True))
    taxes = fields.Nested(tax_schema.Tax(many=True))
    warranty_types = fields.Nested(Misc(many=True))
    manage_stock_types = fields.Nested(Misc(many=True))
    on_off_status = fields.Nested(Misc(many=True))
    colors = fields.Nested(Misc(many=True))
    product_units = fields.Nested(Misc(many=True))
    seo_configs = fields.Nested(Misc(many=True))
    shipping_types = fields.Nested(Misc(many=True))


class ExtraDataRequest(Schema):
    types = fields.String()


class OldBrandSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    internal_code = origin_fields.String()
    url_key = origin_fields.String()


class OldAttributeSetSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()


class OldProductLineSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()


class OldCategorySchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    is_active = origin_fields.Boolean()
    seller_id = origin_fields.Integer()
    parent_id = origin_fields.Integer()
    line_id = origin_fields.Integer()


class OldSaleCategorySchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    parent_id = origin_fields.Integer()
    is_active = origin_fields.Boolean()


class OldColorSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()


class OldUnitSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()


class OldProductUnitSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()


class OldSeoConfigSchema(OriginSchema):
    name = origin_fields.String()
    code = origin_fields.String()


class OldSeoObjectTypeSchema(OriginSchema):
    name = origin_fields.String()
    code = origin_fields.String()


class OldMiscSchema(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()


class OldSellingStatus(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    config = origin_fields.Raw()


class OldEditingStatus(OriginSchema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    config = fields.String()
    can_moved_status = fields.String()
    state_id = fields.Integer()


class OldImportStatus(OriginSchema):
    id = origin_fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    config = origin_fields.Raw()


class OldSellersSchema(OriginSchema):
    id = origin_fields.Integer()
    code = origin_fields.String()
    status = origin_fields.Integer()
    name = origin_fields.String()
    english_name = origin_fields.String()
    enterprise_code = origin_fields.String()
    tax_number = origin_fields.String()
    founding_date = origin_fields.String()
    display_name = origin_fields.String()
    address = origin_fields.String()
    contract_no = origin_fields.String()
    extra_info = origin_fields.Raw()


class OldExtraData(OriginSchema):
    selling_status = origin_fields.Nested(OldSellingStatus, many=True)
    editing_status = origin_fields.Nested(OldEditingStatus, many=True)
    objectives = origin_fields.Nested(OldMiscSchema, many=True)
    product_types = origin_fields.Nested(OldMiscSchema, many=True)
    import_types = origin_fields.Nested(OldMiscSchema, many=True)
    import_status = origin_fields.Nested(OldImportStatus, many=True)
    colors = origin_fields.Nested(OldColorSchema, many=True)
    units = origin_fields.Nested(OldUnitSchema, many=True)
    product_units = origin_fields.Nested(OldProductUnitSchema, many=True)
    warranty_types = origin_fields.Nested(OldMiscSchema, many=True)
    brands = origin_fields.Nested(OldBrandSchema, many=True)
    attribute_sets = origin_fields.Nested(OldAttributeSetSchema, many=True)
    product_lines = origin_fields.Nested(OldProductLineSchema, many=True)
    categories = origin_fields.Nested(OldCategorySchema, many=True)
    sale_categories = origin_fields.Nested(OldSaleCategorySchema, many=True)
    seo_configs = origin_fields.Nested(OldSeoConfigSchema, many=True)
    seo_object_types = origin_fields.Nested(OldSeoObjectTypeSchema, many=True)
    sellers = origin_fields.Nested(OldSellersSchema, many=True)
