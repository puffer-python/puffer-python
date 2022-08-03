CREATE PROCEDURE `setProductJson`(IN `pProductIds` VARCHAR(255))
BEGIN
	 insert into product_details (sku, data, created_at, updated_at)
   select a.sku,
       JSON_OBJECT(
           "sku", a.sku,
           "id", a.id,
           "seller_id", a.seller_id,
           "seller", (select JSON_OBJECT(
                                 "id", sellers.id,
                                 "name", sellers.name,
                                 "display_name", sellers.display_name
                               )
                      from sellers
                      where id = a.seller_id
                      limit 1),
           "name", a.name,
           "url", a.url_key,
           "type", COALESCE((select JSON_OBJECT("code", misc.code, "name", misc.name)
                             from misc
                             where type = 'product_type'
                               and code = a.type
                             limit 1), JSON_OBJECT("code", "product",
                                                   "name", "Sản phẩm vật lý")),
           "objective", COALESCE((select JSON_OBJECT("code", misc.code, "name", misc.name)
                                  from misc
                                  where type = 'objective'
                                    and code = a.objective
                                  limit 1), JSON_OBJECT("code", "gift",
                                                        "name", "Hàng quà tặng")),
           "tax", JSON_OBJECT("tax_out", tax_out,
                              "tax_in", tax_in,
                              "tax_out_code",
                              case tax_out when 10 then "10" when 5 then "5" when 0 then "KT" else "" end,
                              "tax_in_code",
                              case tax_in when 10 then "10" when 5 then "5" when 0 then "KT" else "" end),
           "images", (select JSON_MERGE('[]', concat("[", group_concat(
           JSON_OBJECT(
               "url", pi.url,
               "path", COALESCE(pi.path, ""),
               "priority", pi.priority,
               "label", pi.label
             ) order by pi.priority
         ),
                                                     "]")
                               )
                      from product_images pi
                      where pi.product_id = a.id
                        and pi.is_displayed = 1
                        and pi.status = 1),
           "display_name", COALESCE((select COALESCE(case
                                                       when product_description.display_name is not null or
                                                            product_description.display_name != ""
                                                         then product_description.display_name
                                                       else
                                                         GET_SEO_DATA(a.id, a.attribute_set_id, "seo_name")
                                                       end, ""
                                              )
                                     from product_description
                                     where product_description.product_id = a.id
                                    ), ""),
           "color", (select JSON_OBJECT(
                                "code", code,
                                "name", name
                              )
                     from colors
                     where colors.id = a.color_id
                     limit 1),
           "product_line", (select JSON_OBJECT(
                                       "code", product_lines.code,
                                       "name", product_lines.name
                                     )
                            from product_lines
                            where product_lines.id = a.product_line_id
                            limit 1),
           "channels", COALESCE((select JSON_ARRAYAGG(
                                            JSON_OBJECT(
                                                "id", sale_channels.id,
                                                "code", sale_channels.code,
                                                "name", sale_channels.name,
                                                "type", sale_channels.type
                                              ))
                                 from sale_channel_product
                                        join sale_channels on sale_channels.id = sale_channel_product.channel_id
                                 where sale_channel_product.product_id = a.id), null),
           "attribute_set", (select JSON_OBJECT(
                                        "id", attribute_sets.id,
                                        "name", attribute_sets.name
                                      )
                             from attribute_sets
                             where attribute_sets.id = a.attribute_set_id
                             limit 1),
           "attributes", (select JSON_ARRAYAGG(
                                     JSON_OBJECT(
                                         "id", attributes.id,
                                         "code", attributes.code,
                                         "name", attributes.name,
                                         "priority", d.priority,
                                         "is_searchable", attributes.is_searchable,
                                         "is_filterable", attributes.is_filterable,
                                         "is_comparable", attributes.is_comparable,
                                         "values", (case
                                                      when attributes.value_type = 'multiple_select' then
                                                        COALESCE((select JSON_ARRAYAGG(
                                                                             JSON_OBJECT(
                                                                                 "option_id", o.id,
                                                                                 "value", concat(o.value, COALESCE(
                                                                                 concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                 ""))
                                                                               )
                                                                           )
                                                                  from product_attribute pa
                                                                         JOIN tblIndex
                                                                         join attribute_options o on o.id =
                                                                                                     (SUBSTRING_INDEX(SUBSTRING_INDEX(pa.value, ',', ntIndex), ',', -1))
                                                                    and ntIndex <=
                                                                        1 + LENGTH(pa.value) - LENGTH(REPLACE(pa.value, ',', ''))
                                                                  where pa.product_id = a.id
                                                                    and pa.attribute_id = attributes.id
                                                                 ), JSON_ARRAY())
                                                      ELSE
                                                        COALESCE((select JSON_ARRAYAGG(
                                                                             JSON_OBJECT(
                                                                                 "option_id",
                                                                                 (case when attributes.value_type = "text" then null else o.id end),
                                                                                 "value", (case
                                                                                             when attributes.value_type = "text"
                                                                                               then
                                                                                               concat(pa.value,
                                                                                                      COALESCE(
                                                                                                          concat(" ", (select code from product_units where id = pa.unit_id)),
                                                                                                          ""))
                                                                                             else
                                                                                               concat(o.value,
                                                                                                      COALESCE(
                                                                                                          concat(" ", (select code from product_units where id = o.unit_id)),
                                                                                                          ""))
                                                                               end)
                                                                               )
                                                                           )
                                                                  from product_attribute pa
                                                                         left join attribute_options o on pa.value = o.id
                                                                  where pa.product_id = a.id
                                                                    and pa.attribute_id = attributes.id
                                                                 ), JSON_ARRAY()) end)
                                       ))
                          from attribute_groups e
                                 join attribute_group_attribute d on d.attribute_group_id = e.id
                                 join attributes on d.attribute_id = attributes.id
                          where e.attribute_set_id = a.attribute_set_id
           ),
           "categories", (select JSON_ARRAYAGG(
                                     JSON_OBJECT(
                                         "id", cat1.id,
                                         "code", cat1.code,
                                         "name", cat1.name,
                                         "level", cat1.depth,
                                         "parent_id", cat1.parent_id,
                                         "is_adult", cat1.is_adult
                                       )
                                   )
                          FROM categories cat1
                                 INNER JOIN tblIndex
                          WHERE id = (SUBSTRING_INDEX(SUBSTRING_INDEX(cat.path, '/', ntIndex), '/', -1))
                            and ntIndex <= 1 + LENGTH(cat.path) - LENGTH(REPLACE(cat.path, '/', ''))
           ),
           "seller_categories", (select JSON_ARRAYAGG(
                                            JSON_OBJECT(
                                                "id", cat1.id,
                                                "code", cat1.code,
                                                "name", cat1.name,
                                                "level", cat1.depth,
                                                "parent_id", cat1.parent_id,
                                                "is_adult", cat1.is_adult
                                              )
                                          )
                                 FROM sale_categories cat1
                                        INNER JOIN tblIndex
                                 WHERE id = (SUBSTRING_INDEX(SUBSTRING_INDEX(sale_cat.path, '/', ntIndex), '/', -1))
                                   and ntIndex <= 1 + LENGTH(sale_cat.path) - LENGTH(REPLACE(sale_cat.path, '/', ''))
           ),
           "brand", (select JSON_OBJECT(
                                "id", brands.id,
                                "code", brands.code,
                                "url_key", brands.url_key,
                                "name", brands.name,
                                "description", ""
                              )
                     from brands
                     where brands.id = a.brand_id
           ),
           "status", JSON_OBJECT(
               "selling_status_code", (case
                                         when a.is_bundle = 0 then coalesce(a.selling_status, "hang_dat_truoc")
                                         when a.is_bundle = 1 and a.editing_status in ('active') then "hang_ban"
                                         else "hang_dat_truoc" end),
               "publish_status", (case when a.editing_status in ('active', 'editing') then true else false end),
               "need_manage_stock", round(rand()),
               "priority", (case (case
                                    when a.is_bundle = 0 then coalesce(a.selling_status, "hang_dat_truoc")
                                    when a.is_bundle = 1 and a.editing_status in ('active') then "hang_ban"
                                    else "hang_dat_truoc" end)
                              when "hang_ban" then 1
                              when "hang_sap_het" then 2
                              when "hang_moi" then 3
                              when "hang_trung_bay" then 4
                              when "hang_thanh_ly" then 5
                              when "hang_dat_truoc" then 6
                              when "ngung_kinh_doanh" then 7
                              else 8 end)
             ),
           "smart_showroom", COALESCE(GET_SEO_DATA(a.id, a.attribute_set_id, "smart_showroom"), ""),
           "seo_info", (select JSON_OBJECT(
                                   "meta_keyword", COALESCE(case
                                                              when product_description.meta_keyword is not null or
                                                                   product_description.meta_keyword != ""
                                                                then product_description.meta_keyword
                                                              else
                                                                GET_SEO_DATA(a.id, a.attribute_set_id, "meta_keyword")
                                                              end, ""
             ),
                                   "short_description", COALESCE(case
                                                                   when
                                                                       product_description.short_description is not null or
                                                                       product_description.short_description != ""
                                                                     then product_description.short_description
                                                                   else
                                                                     GET_SEO_DATA(a.id, a.attribute_set_id, "short_description")
                                                                   end, ""
                                     ),
                                   "description", COALESCE(product_description.description, ""),
                                   "meta_title", COALESCE(case
                                   "meta_title", COALESCE(case
                                                            when product_description.meta_title is not null or
                                                                 product_description.meta_title != ""
                                                              then product_description.meta_title
                                                            else
                                                              GET_SEO_DATA(a.id, a.attribute_set_id, "meta_title")
                                                            end, ""
                                     ),
                                   "meta_description", COALESCE(case
                                                                  when
                                                                      product_description.meta_description is not null or
                                                                      product_description.meta_description != ""
                                                                    then product_description.meta_description
                                                                  else
                                                                    GET_SEO_DATA(a.id, a.attribute_set_id, "meta_description")
                                                                  end, ""
                                     )
                                 )
                        from product_description
                        where product_description.product_id = a.id
           ),
           "warranty", JSON_OBJECT(
               "months", a.warranty_months,
               "description", a.warranty_description
             ),
           "created_at", a.created_at,
           "bundle_products", (select JSON_ARRAYAGG(
                                          JSON_OBJECT(
                                              "sku", products.sku,
                                              "quantity", product_bundles.quantity,
                                              "priority", product_bundles.priority,
                                              "name", products.name,
                                              "seo_name",
                                              GET_SEO_DATA(products.id, products.attribute_set_id, "seo_name")
                                            )
                                        )
                               from products
                                      join product_bundles on products.id = product_bundles.product_id
                               where product_bundles.bundle_product_id = a.id
           ),
           "parent_bundles", (select JSON_ARRAYAGG(
                                         JSON_OBJECT(
                                             "sku", products.sku,
                                             "name", products.name
                                           )
                                       )
                              from products
                                     join product_bundles on products.id = product_bundles.bundle_product_id
                              where product_bundles.product_id = a.id
           ),
           "tags", JSON_ARRAY(),
           "is_bundle", a.is_bundle,
           "attribute_groups", `ATTRIBUTE_GROUP`(`a`.`id`, `a`.`attribute_set_id`),
           "product_group", `PRODUCT_GROUP`(a.product_group_id, `a`.`attribute_set_id`),
           "serial_managed", round(rand()),
           "serial_generated", 1,
           "bar_code", a.barcode,
           "uom", (
             SELECT ppm.name
             from units ppm
             where a.unit_id = ppm.id
           ),
           "terminals", COALESCE((select JSON_ARRAYAGG(
                                             sale_terminals.code
                                           )
                                  from sale_channel_product
                                         JOIN sale_terminals
                                              on sale_channel_product.channel_id = sale_terminals.channel_id
                                  where sale_channel_product.product_id = a.id), null)
         ) product_json,
       now(),
       now()
from products a
       left join categories cat on a.category_id = cat.id
       left join sale_category_product sale_cat_product
                 on a.id = sale_cat_product.product_id and sale_cat_product.sale_category_id is not null
       left join sale_categories sale_cat on sale_cat.id = sale_cat_product.sale_category_id
       INNER JOIN tblIndex
       left join product_properties_movesrm on product_properties_movesrm.sku = a.sku
										WHERE a.id = (SUBSTRING_INDEX(SUBSTRING_INDEX(pProductIds, ',', ntIndex), ',', -1))
										and ntIndex <= 1 + LENGTH(pProductIds) - LENGTH(REPLACE(pProductIds,',',''))
	   ON DUPLICATE KEY UPDATE
			 data = VALUES(data),
			 updated_at = now();
END