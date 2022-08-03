from catalog.services.products import ProductVariantService

_variant_service = ProductVariantService.get_instance()


def create_variants(product_id, tuple_variants, created_by):
    data_not_variants = []
    for variant_attributes, not_variant_attributes, variant_id in tuple_variants:
        if not variant_id:
            upsert_variants = _variant_service.create_variants(
                product_id, variant_attributes, created_by, __not_bulk_commit=True)
            variant_id = upsert_variants[0].get('id')
        data_not_variants.append({
            'variant_id': variant_id,
            'attributes': not_variant_attributes
        })
    return data_not_variants
