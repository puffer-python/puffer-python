CREATE FUNCTION `ATTRIBUTE_GROUP_V2`(pSellable_id int, pVariant_id int, pAttribute_set_id int) RETURNS json
BEGIN
    RETURN COALESCE((select JSON_ARRAYAGG(
                                    JSON_OBJECT(
                                            "id", t.id,
                                            "name", t.name,
                                            "value", t.value,
                                            "priority", t.priority,
                                            "parent_id", t.parent_id
                                        )
                                )
                     from (
                              select attribute_groups.id,
                                     attribute_groups.parent_id,
                                     attribute_groups.priority,
                                     attribute_groups.name,
                                     GROUP_CONCAT(concat(COALESCE(concat(text_before, " "), " "), (CASE
                                                                                                       WHEN attributes.value_type = 'multiple_select'
                                                                                                           THEN
                                                                                                           (select group_concat(
                                                                                                                           concat(
                                                                                                                                   o.value,
                                                                                                                                   COALESCE(
                                                                                                                                           concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                                                                           ""))
                                                                                                                           SEPARATOR
                                                                                                                           ", ")
                                                                                                            from variant_attribute va
                                                                                                                     JOIN tblIndex
                                                                                                                     join attribute_options o
                                                                                                                          on o.id =
                                                                                                                             (SUBSTRING_INDEX(SUBSTRING_INDEX(va.value, ',', ntIndex), ',', -1))
                                                                                                                              and
                                                                                                                             ntIndex <=
                                                                                                                             1 + LENGTH(va.value) - LENGTH(REPLACE(va.value, ',', ''))
                                                                                                            where va.variant_id = pVariant_id
                                                                                                              and va.attribute_id = attributes.id
                                                                                                              and o.value <> 'KHT')
                                                                                                       ELSE
                                                                                                           (select case
                                                                                                                       when attributes.value_type in ("text", "number")
                                                                                                                           then
                                                                                                                           concat(
                                                                                                                                   va.value,
                                                                                                                                   COALESCE(
                                                                                                                                           concat(" ", (select code from product_units where id = va.unit_id)),
                                                                                                                                           ""))
                                                                                                                       else
                                                                                                                           concat(
                                                                                                                                   o.value,
                                                                                                                                   COALESCE(
                                                                                                                                           concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                                                                           ""))
                                                                                                                       end
                                                                                                            from variant_attribute va
                                                                                                                     left join attribute_options o on va.value = o.id and o.value <> 'KHT'
                                                                                                            where va.variant_id = pVariant_id
                                                                                                              and va.attribute_id = attributes.id
                                                                                                              and trim(va.value) <> 'KHT'
                                                                                                           )
                                         END),
                                                         COALESCE(concat(" ", case
                                                                                  when IS_LAST_NOT_LAST_V2(pVariant_id, attribute_groups.id, attributes.id)
                                                                                      then null
                                                                                  else text_after end), " "))
                                                  ORDER BY aga.priority SEPARATOR "") as value
                              from attribute_groups
                                       left join attribute_group_attribute aga
                                                 on attribute_groups.id = aga.attribute_group_id and aga.is_displayed = 1
                                       left join attributes on aga.attribute_id = attributes.id
                              where attribute_groups.attribute_set_id = pAttribute_set_id
                                and attribute_groups.is_flat = 0
                              group by attribute_groups.id
                              union all
                              select null id, parent_id, priority, name, value
                              from (
                                       select attribute_groups.id  parent_id,
                                              0                    priority,
                                              "Thương hiệu"        name,
                                              coalesce(b.name, "") value
                                       from attribute_groups
                                                left join (select a.attribute_set_id, b.name
                                                           from sellable_products a
                                                                    join brands b on a.brand_id = b.id
                                                           where a.id = pSellable_id) b
                                                          on b.attribute_set_id = attribute_groups.attribute_set_id
                                       where attribute_groups.attribute_set_id = pAttribute_set_id
                                         and code = 'thong-tin-chung'
                                       union all
                                       select attribute_groups.id parent_id,
                                              1                   priority,
                                              "Bảo hành"          name,
                                              b.warranty_months   value
                                       from attribute_groups
                                                left join (select attribute_set_id, warranty_months
                                                           from sellable_products
                                                           where id = pSellable_id) b
                                                          on b.attribute_set_id = attribute_groups.attribute_set_id
                                       where attribute_groups.attribute_set_id = pAttribute_set_id
                                         and code = 'thong-tin-chung'
                                       union all
                                       select attribute_groups.id parent_id,
                                              2                   priority,
                                              "Mô tả bảo hành"    name,
                                              b.warranty_note     value
                                       from attribute_groups
                                                left join (select attribute_set_id, warranty_note
                                                           from sellable_products
                                                           where id = pSellable_id) b
                                                          on b.attribute_set_id = attribute_groups.attribute_set_id
                                       where attribute_groups.attribute_set_id = pAttribute_set_id
                                         and code = 'thong-tin-chung'
                                   ) t
                              where value is not null
                              union
                              select attribute_groups.id,
                                     attribute_groups.parent_id,
                                     attribute_groups.priority,
                                     attribute_groups.name,
                                     "" as value
                              from attribute_groups
                              where (exists(select 1
                                            from attribute_group_attribute
                                            where is_displayed = 1
                                              and attribute_group_id = attribute_groups.id
                                              and attribute_groups.is_flat = 1)
                                  or exists(select 1
                                            from attribute_groups a
                                            where a.parent_id = attribute_groups.id
                                              and attribute_groups.is_flat = 1)
                                  or attribute_groups.code = 'thong-tin-chung'
                                  )
                                and attribute_groups.attribute_set_id = pAttribute_set_id
                              union
                              select null                                 as id,
                                     attribute_groups.id,
                                     aga.priority,
                                     case
                                         when attributes.display_name is null or attributes.display_name = ""
                                             then attributes.name
                                         else attributes.display_name end as name,
                                     case
                                         when attributes.value_type in ("text", "number") then
                                             concat(va.value, COALESCE(
                                                     concat(" ", (select code from product_units where id = va.unit_id)),
                                                     ""))
                                         else
                                             (SELECT group_concat(
                                                             concat(
                                                                     o.value,
                                                                     COALESCE(
                                                                             concat(" ",
                                                                                    (SELECT code
                                                                                     FROM product_units
                                                                                     WHERE id = o.unit_id)),
                                                                             "")
                                                                 ) SEPARATOR ", ")
                                              FROM variant_attribute va
                                                       JOIN tblIndex
                                                       JOIN attribute_options o ON o.id =
                                                                                   (SUBSTRING_INDEX(SUBSTRING_INDEX(va.value, ',', ntIndex), ',', -1))
                                                  AND ntIndex <=
                                                      1 + LENGTH(va.value) - LENGTH(REPLACE(va.value, ',', ''))
                                              WHERE va.variant_id = pVariant_id
                                                AND va.attribute_id = attributes.id
                                                AND o.value <> 'KHT'
                                             )
                                         end                              as value
                              from attribute_groups
                                       left join (select * from attribute_group_attribute where is_displayed = 1) aga
                                                 on attribute_groups.id = aga.attribute_group_id
                                       left join variant_attribute va on va.attribute_id = aga.attribute_id
                                       left join attributes on aga.attribute_id = attributes.id
                              where attribute_groups.attribute_set_id = pAttribute_set_id
                                and attribute_groups.is_flat = 1
                                and variant_id = pVariant_id
                                and va.value <> 'KHT'
                              order by priority
                          ) t
                     where t.value is not null), JSON_ARRAY());
END