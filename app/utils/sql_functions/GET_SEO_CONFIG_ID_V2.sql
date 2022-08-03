CREATE FUNCTION `GET_SEO_CONFIG_ID_V2`(`pSellable_id` INT, `pAttribute_set_id` INT, pIs_default INT) RETURNS int(11)
    READS SQL DATA
BEGIN
    RETURN (select a.id
            from sellable_products b
                     join attribute_set_config a
                          on a.attribute_set_id = b.attribute_set_id and (a.brand_id = b.brand_id or a.brand_id is null)
                     left join variant_attribute c
                               on b.variant_id = c.variant_id and a.attribute_1_id = c.attribute_id and
                                  a.attribute_1_value = c.value
                     left join variant_attribute d
                               on b.variant_id = d.variant_id and a.attribute_2_id = d.attribute_id and
                                  a.attribute_2_value = d.value
                     left join variant_attribute e
                               on b.variant_id = e.variant_id and a.attribute_3_id = e.attribute_id and
                                  a.attribute_3_value = e.value
                     left join variant_attribute f
                               on b.variant_id = f.variant_id and a.attribute_4_id = f.attribute_id and
                                  a.attribute_4_value = f.value
                     left join variant_attribute g
                               on b.variant_id = g.variant_id and a.attribute_5_id = g.attribute_id and
                                  a.attribute_5_value = g.value
            where b.attribute_set_id = pAttribute_set_id
              and b.id = pSellable_id
              and (
                    (is_default = pIs_default and is_default = 1) or (
                        a.is_deleted = 0
                        and (concat((case when a.attribute_1_id is not null then 2 else 0 end),
                                    (case when a.attribute_2_id is not null then 2 else 0 end),
                                    (case when a.attribute_3_id is not null then 2 else 0 end),
                                    (case when a.attribute_4_id is not null then 2 else 0 end),
                                    (case when a.attribute_5_id is not null then 2 else 0 end)) -
                             concat((case when c.attribute_id is not null then 2 else 0 end),
                                    (case when d.attribute_id is not null then 2 else 0 end),
                                    (case when e.attribute_id is not null then 2 else 0 end),
                                    (case when f.attribute_id is not null then 2 else 0 end),
                                    (case when g.attribute_id is not null then 2 else 0 end)) +
                             coalesce(a.brand_id, coalesce(b.brand_id, 0)) - coalesce(b.brand_id, 0)) = 0
                    )
                )
            order by g.attribute_id desc, f.attribute_id desc, e.attribute_id desc, d.attribute_id desc,
                     c.attribute_id desc, a.brand_id desc
            limit 1);
END