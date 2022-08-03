CREATE FUNCTION `PRODUCT_GROUP_V2`(`pProduct_id` INT, `pVariant_id` INT, `pAttribute_Set_id` INT) RETURNS json
    READS SQL DATA
BEGIN
    RETURN
        CASE
            WHEN pProduct_id is null OR pProduct_id = 0 THEN
                CAST('null' AS JSON)
            ELSE
                COALESCE((

                SELECT json_object("id", b.id, "name", b.name, "visible", 'individual', "configurations",
                                             (
                                                 SELECT JSON_MERGE('[]', concat("[", group_concat(
                                                         JSON_OBJECT("id", attributes.id,
                                                                     "code", attributes.code,
                                                                     "name",
                                                                     COALESCE(NULLIF(attributes.display_name, ''), attributes.name),
                                                                     "option_type",
                                                                     attribute_group_attribute.variation_display_type,
                                                                     "options",
                                                                     (
                                                                         SELECT JSON_MERGE('[]', (concat('[',group_concat(JSON_OBJECT(
                                                                                 "value",
                                                                                 COALESCE(
                                                                                         NULLIF(attribute_options.display_value, ''),
                                                                                         attribute_options.value),
                                                                                 "option_id",
                                                                                 attribute_options.id,
                                                                                 "thumbnail_url", attribute_options.thumbnail_url,
                                                                                 "image", CASE
                                                                                              WHEN attribute_group_attribute.variation_display_type = 'image'
                                                                                                  THEN (COALESCE(
                                                                                                      (SELECT JSON_OBJECT(
                                                                                                                      "url",
                                                                                                                      variant_images.url,
                                                                                                                      "priority",
                                                                                                                      variant_images.priority,
                                                                                                                      "path",
                                                                                                                      variant_images.path)
                                                                                                       FROM product_variants
                                                                                                                JOIN variant_images
                                                                                                                     ON product_variants.id = variant_images.product_variant_id
                                                                                                                JOIN variant_attribute ON product_variants.id = variant_attribute.variant_id
                                                                                                       WHERE variant_attribute.value = attribute_options.id
                                                                                                         AND variant_images.status = 1
                                                                                                         AND product_variants.product_id = b.id
                                                                                                       ORDER BY variant_images.priority ASC
                                                                                                       LIMIT 1),
                                                                                                      cast('null' AS JSON)))
                                                                                              ELSE cast('null' AS JSON)
                                                                                     END) order by attribute_options.priority),']')))
                                                                         FROM attribute_options
                                                                         WHERE attribute_options.id in (
                                                                             SELECT value
                                                                             from variant_attribute
                                                                                      left join product_variants pv on variant_attribute.variant_id = pv.id
                                                                             where variant_attribute.attribute_id = attributes.id
                                                                               and pv.product_id = pProduct_id
                                                                         )
                                                                     )
                                                             )
                                                     ), "]"))
                                                 FROM attributes
                                                          JOIN attribute_group_attribute
                                                               ON attributes.id = attribute_group_attribute.attribute_id
                                                          JOIN attribute_groups
                                                               ON attribute_groups.id = attribute_group_attribute.attribute_group_id
                                                 WHERE attribute_group_attribute.is_variation = 1
                                                   AND IF(is_uom.id, attributes.code not in ('uom_ratio'),
                                                          attributes.code not in ('uom_ratio', 'uom'))
                                                   AND attribute_groups.attribute_set_id = pAttribute_Set_id
                                             ),
                                             "variants",
                                             (SELECT JSON_ARRAYAGG(JSON_OBJECT("sku", a.sku, "attribute_values",
                                                                               (SELECT JSON_ARRAYAGG(
                                                                                               JSON_OBJECT("id",
                                                                                                           variant_attribute.id,
                                                                                                           "code",
                                                                                                           attributes.code,
                                                                                                           "value",
                                                                                                           concat(
                                                                                                                   IF(
                                                                                                                           attributes.code = 'uom' AND a.uom_ratio <> 1,
                                                                                                                           (
                                                                                                                               SELECT IF(
                                                                                                                                              sps.uom_code = a.uom_code,
                                                                                                                                              concat(a.uom_ratio, ' ', sps.uom_name),
                                                                                                                                              concat(a.uom_name, ' ', a.uom_ratio, ' ', sps.uom_name)
                                                                                                                                          )
                                                                                                                               FROM sellable_products sps
                                                                                                                               WHERE sps.uom_ratio = 1
                                                                                                                                 AND sps.product_id = pProduct_id
                                                                                                                               LIMIT 1
                                                                                                                           ),
                                                                                                                           COALESCE(
                                                                                                                                   NULLIF(attribute_options.display_value, ''),
                                                                                                                                   attribute_options.value
                                                                                                                               )
                                                                                                                       )),
                                                                                                           "option_id",
                                                                                                           attribute_options.id))
                                                                                FROM variant_attribute
                                                                                         JOIN attributes ON variant_attribute.attribute_id = attributes.id
                                                                                         JOIN attribute_options ON variant_attribute.value = attribute_options.id
                                                                                         JOIN attribute_group_attribute
                                                                                              ON attributes.id = attribute_group_attribute.attribute_id
                                                                                         JOIN attribute_groups
                                                                                              ON attribute_groups.id = attribute_group_attribute.attribute_group_id
                                                                                WHERE attribute_group_attribute.is_variation = 1
                                                                                  AND variant_attribute.variant_id = a.variant_id
                                                                                  AND attribute_options.id IS NOT NULL
                                                                                  and IF(is_uom.id,
                                                                                         attributes.code not in ('uom_ratio'),
                                                                                         attributes.code not in ('uom_ratio', 'uom'))
                                                                                  AND attribute_groups.attribute_set_id = pAttribute_Set_id)))
                                              FROM sellable_products a
                                                       JOIN
                                                   (SELECT a.product_id, count(1) sl
                                                    FROM sellable_products a
                                                             JOIN product_variants b ON a.variant_id = b.id
                                                        AND a.product_id = pProduct_id
                                                    GROUP BY a.product_id) b
                                              WHERE a.product_id = pProduct_id
                                                AND a.editing_status_code = 'active'
                                                AND (a.selling_status_code <> 'ngung_kinh_doanh' OR a.selling_status_code is null)
                                                AND b.sl > 1)
                                     )
                          FROM products b
                                   left join
                               (SELECT uom_check.id AS id
                                FROM sellable_products uom_check
                                WHERE uom_check.product_id = pProduct_id
                                  AND uom_check.uom_ratio <> 1
                                LIMIT 1) as is_uom on 1
                                   left join
                               (SELECT base_uoms.variant_id AS variant_id,
                                       base_uoms.id         as id,
                                       base_uoms.unit_id,
                                       base_uoms.uom_code
                                FROM sellable_products base_uoms
                                WHERE base_uoms.product_id = pProduct_id
                                  AND base_uoms.uom_ratio = 1
                                LIMIT 1) as bas_uom on 1
                          WHERE b.id = pProduct_id


                          ), CAST('null' AS JSON))
            END;
END
