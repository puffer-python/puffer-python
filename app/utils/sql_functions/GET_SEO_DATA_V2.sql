CREATE FUNCTION `GET_SEO_DATA_V2`(`pSellable_id` INT, `pVariant_id` INT, `pAttributeSetId` INT,
                                --   `pSeoType` VARCHAR(255) CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci, -- For deploy
                                  `pSeoType` VARCHAR(255), -- For testing
                                  is_default INT) RETURNS text CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci
    READS SQL DATA
BEGIN
    DECLARE configId INT(11); SET configId = GET_SEO_CONFIG_ID_V2(pSellable_id, pAttributeSetId, is_default);
    RETURN (select group_concat(concat(COALESCE(text_before, ""), case
                                                                      when object_type = 'product_name' then d.name
                                                                      when object_type = 'attribute_set' then COALESCE(
                                                                                  (select name from attribute_sets where id = d.attribute_set_id limit 1),
                                                                                  "")
                                                                      when object_type = 'brand'
                                                                          then COALESCE((select name from brands where id = d.brand_id limit 1), "")
                                                                      when object_type = 'sku' then d.sku
                                                                      when object_type = 'warranty'
                                                                          then concat(d.warranty_months, " tháng")
                                                                      when object_type = 'model' then d.model
                                                                      when object_type = 'part_number'
                                                                          then d.part_number
                                                                      when object_type = 'text' then a.object_value
                                                                      else (CASE
                                                                                WHEN attributes.value_type = 'multiple_select'
                                                                                    THEN (select group_concat(
                                                                                                         concat(o.value,
                                                                                                                COALESCE(
                                                                                                                        concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                                                        ""))
                                                                                                         SEPARATOR ", ")
                                                                                          from variant_attribute va
                                                                                                   JOIN tblIndex
                                                                                                   join attribute_options o
                                                                                                        on o.id =
                                                                                                           (SUBSTRING_INDEX(SUBSTRING_INDEX(va.value, ',', ntIndex), ',', -1)) and
                                                                                                           ntIndex <=
                                                                                                           1 + LENGTH(va.value) - LENGTH(REPLACE(va.value, ',', ''))
                                                                                          where va.variant_id = pVariant_id
                                                                                            and va.attribute_id = attributes.id
                                                                                            and o.value <> 'KHT')
                                                                                ELSE (select case
                                                                                                 when attributes.value_type = "text"
                                                                                                     then concat(
                                                                                                         va.value,
                                                                                                         COALESCE(
                                                                                                                 concat(" ", (select code from product_units where id = va.unit_id)),
                                                                                                                 ""))
                                                                                                 else concat(o.value,
                                                                                                             COALESCE(
                                                                                                                     concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                                                     "")) end
                                                                                      from variant_attribute va
                                                                                               left join attribute_options o on va.value = o.id and o.value <> 'KHT'
                                                                                      where va.variant_id = pVariant_id
                                                                                        and va.attribute_id = attributes.id
                                                                                        and trim(va.value) <> 'KHT') END) end,
                                       COALESCE(text_after, "")) ORDER BY a.priority SEPARATOR "")
            from attribute_set_config_detail a
                     left join attributes on attributes.id = a.object_value
                     join sellable_products d on d.id = pSellable_id
            where attribute_set_config_id = configId
              and field_display = pSeoType);
END