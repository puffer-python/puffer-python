  select a.sku,
         JSON_OBJECT(
           "sku", a.sku,
           "seller_sku", a.seller_sku,
           "uom_code", a.uom_code,
           "uom_name", a.uom_name,
           "uom_ratio", CAST(a.uom_ratio as CHAR),
           "id", a.id,
           "seller_id", a.seller_id,
           "seller",(
             select JSON_OBJECT("id", sellers.id, "name", sellers.name, "display_name", sellers.display_name)
             from sellers
             where id = a.seller_id
             limit 1),
           "provider",JSON_OBJECT(
                        "id", a.provider_id
            ),
           "name", a.name,
           "url", COALESCE((select case
                        when url_key is not null and url_key != "" then url_key
                        else
                            null
                        end
                from products where id = a.product_id), b.url_key),
           "barcode", a.barcode,
           "barcodes", (select JSON_ARRAYAGG(JSON_OBJECT("barcode", spb.barcode, "source", spb.source, "is_default", spb.is_default))
                        from sellable_product_barcodes spb
                        where spb.sellable_product_id = a.id),
           "type",
                     COALESCE((select JSON_OBJECT("code", misc.code, "name", misc.name)
                               from misc
                               where type = 'product_type'
                                 and code = a.product_type
                               limit 1), JSON_OBJECT("code", "product", "name", "Sản phẩm vật lý")),
           "tax", (SELECT JSON_OBJECT("tax_in_code", taxes.code, 'tax_in', CAST(taxes.amount as UNSIGNED))
                            FROM taxes WHERE taxes.code = a.tax_in_code LIMIT 1),
           "images",
                     (select JSON_ARRAYAGG(JSON_OBJECT("url", vi.url, "path", COALESCE(vi.path, ""), "priority", vi.priority, "label", vi.label))
                      from variant_images vi
                      where vi.product_variant_id = b.id
                        order by vi.priority
                        and vi.status = 1 and vi.is_displayed = 1),
           "display_name", COALESCE((select COALESCE(case
                        when display_name is not null and display_name != "" then display_name
                        end,""
                ) from products where id = a.product_id
            ),""),
            "color",
                     (select JSON_OBJECT("code", code, "name", name) from colors where colors.id = a.color_id limit 1),
           "product_line", JSON_OBJECT(),
           "channels", null,
           "attribute_set",
                     (select JSON_OBJECT("id", attribute_sets.id, "name", attribute_sets.name)
                      from attribute_sets
                      where attribute_sets.id = a.attribute_set_id
                      limit 1),
           "attributes", (select JSON_ARRAYAGG(
              JSON_OBJECT(
                  "id", attributes.id,
                  "code", attributes.code,
                  "name", (case when attributes.display_name is not null and attributes.display_name <> "" then attributes.display_name else attributes.name end),
                  "priority", d.priority,
                  "is_searchable", attributes.is_searchable,
                  "is_filterable", attributes.is_filterable,
                  "is_comparable", attributes.is_comparable,
                  "values", (case
                                       when attributes.value_type = 'multiple_select'
                                         then COALESCE(
                                           (select JSON_ARRAYAGG(
                                                       JSON_OBJECT(
                                                           "option_id",
                                                           o.id, "value",
                                                           concat(o.value,
                                                                  COALESCE(
                                                                      concat(" ", (select code from product_units where id = o.unit_id)),
                                                                      ""))))
                                            from variant_attribute va
                                                   INNER JOIN tblIndex
                                                   join attribute_options o
                                                        on o.id =
                                                           (SUBSTRING_INDEX(SUBSTRING_INDEX(va.value, ',', ntIndex), ',', -1)) and
                                                           ntIndex <=
                                                           1 + LENGTH(va.value) - LENGTH(REPLACE(va.value, ',', ''))
                                            where va.variant_id = b.id
                                              and o.value <> 'KHT'
                                              and va.attribute_id = attributes.id),
                                           JSON_ARRAY())
                                       when attributes.code in ("pack_weight", "pack_height", "pack_width", "pack_length")
                                         then COALESCE(
                                         (select JSON_ARRAYAGG(
                                                     JSON_OBJECT(
                                                         "option_id", null,
                                                         "value", concat(attribute_json.value, COALESCE(
                                                             concat(" ", (select code from product_units where id = attribute_json.unit_id)),
                                                             ""))))
                                          from (select va.* from variant_attribute va
                                                                left join attributes a2 on va.attribute_id = a2.id
                                          where va.variant_id = b.id and va.value != "KHT"
                                            and (a2.code = replace(attributes.code, "pack_", "") or a2.code = attributes.code)
                                            order by reverse(a2.code) desc
                                            limit 1) attribute_json),
                                         JSON_ARRAY())
                                       ELSE COALESCE((select JSON_ARRAYAGG(
                                                                 JSON_OBJECT(
                                                                     "option_id",
                                                                     (case when attributes.value_type in ("text", "number") then null else o.id end),
                                                                     "value",
                                                                     (case
                                                                        when attributes.value_type in ("text", "number")
                                                                          then concat(
                                                                            va.value,
                                                                            COALESCE(
                                                                                concat(" ", (select code from product_units where id = va.unit_id)),
                                                                                ""))
                                                                        else concat(
                                                                            o.value,
                                                                            COALESCE(
                                                                                concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                "")) end)))
                                                      from variant_attribute va
                                                             left join attribute_options o on va.value = o.id
                                                      where va.variant_id = b.id and va.value <> 'KHT' and o.value <> 'KHT'
                                                        and va.attribute_id = attributes.id),
                                                     JSON_ARRAY()) end)))
               from attribute_groups e
                      join attribute_group_attribute d on d.attribute_group_id = e.id
                      join attributes on d.attribute_id = attributes.id
               where e.attribute_set_id = a.attribute_set_id),
           "categories",
                     (select JSON_ARRAYAGG(
                                 JSON_OBJECT("id", cat1.id, "code", cat1.code, "name", cat1.name, "level", cat1.depth,
                                             "parent_id", cat1.parent_id, "is_adult", cat1.is_adult))
                      FROM categories cat1
                             INNER JOIN tblIndex
                      WHERE id = (SUBSTRING_INDEX(SUBSTRING_INDEX(default_cat.path, '/', ntIndex), '/', -1))
                        and ntIndex <= 1 + LENGTH(default_cat.path) - LENGTH(REPLACE(default_cat.path, '/', ''))),
           "platform_categories",
                    (select JSON_ARRAYAGG(JSON_OBJECT("platform_id", p.platform_id, "owner_seller_id", cat.seller_id, "categories",
                     (select JSON_ARRAYAGG(
                                 JSON_OBJECT("id", cat1.id, "code", cat1.code, "name", cat1.name, "level", cat1.depth,
                                             "parent_id", cat1.parent_id, "is_adult", cat1.is_adult))
                      FROM categories cat1
                             INNER JOIN tblIndex
                      WHERE id = (SUBSTRING_INDEX(SUBSTRING_INDEX(cat.path, '/', ntIndex), '/', -1))
                        and ntIndex <= 1 + LENGTH(cat.path) - LENGTH(REPLACE(cat.path, '/', '')))))
                      FROM product_categories product_cat
                      INNER JOIN categories cat ON product_cat.category_id = cat.id
                      INNER JOIN platform_sellers p ON cat.seller_id = p.seller_id AND p.is_owner = 1
                        WHERE product_cat.product_id = a.product_id),
           "seller_categories",
                     (select JSON_ARRAYAGG(
                                 JSON_OBJECT("id", cat1.id, "code", cat1.code, "name", cat1.name, "level", cat1.depth,
                                             "parent_id", cat1.parent_id))
                      FROM master_categories cat1
                             INNER JOIN tblIndex
                      WHERE id = (SUBSTRING_INDEX(SUBSTRING_INDEX(master_cat.path, '/', ntIndex), '/', -1))
                        and ntIndex <= 1 + LENGTH(master_cat.path) - LENGTH(REPLACE(master_cat.path, '/', ''))),
           "brand",
                     (select JSON_OBJECT("id", brands.id, "code", brands.code, "name",
                                         brands.name, "description", "")
                      from brands
                      where brands.id = a.brand_id),
           "status", JSON_OBJECT("selling_status_code", (case
                                                                                                     when a.is_bundle = 0
                                                                                                       then coalesce(a.selling_status_code, "hang_ban")
                                                                                                     when a.is_bundle = 1 and a.editing_status_code in ('active')
                                                                                                       then "hang_ban"
                                                                                                     else "hang_ban" end),
           "editing_status", a.editing_status_code,
           "publish_status", (case
                                when a.editing_status_code in ('active', 'editing')
                                  then true
                                else false end),
           "need_manage_stock", 1,
           "priority", (case (case
                                when a.is_bundle = 0
                                  then coalesce(a.selling_status_code, "hang_dat_truoc")
                                when a.is_bundle = 1 and a.editing_status_code in ('active')
                                  then "hang_ban"
                                else "hang_dat_truoc" end)
                          when "hang_ban" then 1
                          when "hang_sap_het" then 2
                          when "hang_moi" then 3
                          when "hang_trung_bay" then 4
                          when "hang_thanh_ly" then 5
                          when "hang_dat_truoc" then 6
                          when "ngung_kinh_doanh" then 7
                          else 8 end)),
           "smart_showroom", COALESCE(GET_SEO_DATA_V2(a.id, a.variant_id, a.attribute_set_id, "smart_showroom", 1),""),
           "seo_info", (select JSON_OBJECT(
                "meta_keyword", COALESCE(p.meta_keyword,""),
                "short_description", "",
                "description", "",
                "meta_title", COALESCE(p.meta_title,""),
                "meta_description", COALESCE(p.meta_description,"")
             )
              from products p
              where p.id = a.product_id),
           "warranty",
                     JSON_OBJECT("months", a.warranty_months, "description", a.warranty_note),
           "created_at", a.created_at,
           "bundle_products", (select JSON_ARRAYAGG(JSON_OBJECT(
                "sku", sellable_products.sku,
                "quantity", sellable_product_bundles.quantity,
                "priority", sellable_product_bundles.priority,
                "name", sellable_products.name,
                "seo_name", null))
              from sellable_products
              join sellable_product_bundles on sellable_products.id = sellable_product_bundles.sellable_product_id
              where sellable_product_bundles.bundle_id = a.id),
            "parent_bundles", (select JSON_ARRAYAGG(JSON_OBJECT(
                "sku", sellable_products.sku,
                "name", sellable_products.name))
               from sellable_products
               join sellable_product_bundles on sellable_products.id = sellable_product_bundles.bundle_id
                                        where sellable_product_bundles.sellable_product_id = a.id),
           "tags", IF( spt.tags IS NULL, CAST("[]" AS JSON), CAST(
                  CONCAT('["', REPLACE(spt.tags, ',', '","'), '"]')
              AS JSON)),
           "is_bundle", a.is_bundle,
           "attribute_groups", `ATTRIBUTE_GROUP_V2`(`a`.`id`, `a`.`variant_id`, `a`.`attribute_set_id`),
           "product_group", `PRODUCT_GROUP_V2`(`a`.`product_id`, `a`.`variant_id`, `a`.`attribute_set_id`),
           "serial_managed", a.tracking_type,
           "serial_generated", a.auto_generate_serial,
           "terminals", JSON_ARRAY(),
           "terminal_groups", (select JSON_ARRAYAGG(terminal_group_code) from sellable_product_terminal_group
                                    where sellable_product_terminal_group.sellable_product_id = a.id),
           "manufacture", (
           select JSON_OBJECT(
                                "id", attribute_options.id,
                                "code", IFNULL(attribute_options.code, variant_attribute.value),
                                "name", attribute_options.value) from variant_attribute left join
                                attributes on variant_attribute.attribute_id = attributes.id
                                left join attribute_options
                                        on attribute_options.attribute_id = attributes.id
                                            and variant_attribute.value = attribute_options.id
                                where attributes.code = 'manufacture'
                                    and variant_attribute.variant_id = a.variant_id limit 1),
           "shipping_type",  (select st.code from sellable_product_shipping_type spst
                                    join shipping_types st
                                        on spst.shipping_type_id = st.id where sellable_product_id = a.id limit 1),
            "ppm_info", (SELECT JSON_OBJECT("selling_status", sellable_product_price.selling_status,
                                            "terminal_group_ids", CAST(sellable_product_price.terminal_group_ids as JSON),
                                            "selling_price", sellable_product_price.selling_price)
                            FROM sellable_product_price where sellable_product_price.sellable_product_id = a.id LIMIT 1)
    ) product_json
  from sellable_products a
         left join product_variants b on a.variant_id = b.id
         left join categories default_cat on a.category_id = default_cat.id
         left join master_categories master_cat on master_cat.id = a.master_category_id
         left join sellable_product_tags spt on a.id = spt.sellable_product_id
