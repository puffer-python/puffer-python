CREATE FUNCTION `IS_LAST_NOT_LAST_V2`(`pVariant_id` INT, `pAttribute_group_id` INT, `pAttribute_id` INT) RETURNS tinyint(1)
    READS SQL DATA
BEGIN
    RETURN (
        select case
                   when a.priority < b.last_current then false
                   when a.priority = b.last_current and b.last_current = c.last_all then false
                   else true
                   end
        from attribute_group_attribute a
                 join (select b.attribute_group_id,
                              max(case
                                      when c.id is null and d.value_type != 'text' then b.priority = -1
                                      else b.priority end) last_current
                       from variant_attribute a
                                left join attribute_options c
                                          on a.value = c.id and a.value <> 'KHT' and c.value <> 'KHT'
                                join attribute_group_attribute b
                                     on a.attribute_id = b.attribute_id and a.variant_id = pVariant_id and
                                        b.attribute_group_id = pAttribute_group_id
                                join attributes d on b.attribute_id = d.id) b
                      on a.attribute_group_id = b.attribute_group_id
                 join (select aga.attribute_group_id, max(priority) last_all
                       from attribute_group_attribute aga
                       where aga.attribute_group_id = pAttribute_group_id) c
                      on a.attribute_group_id = c.attribute_group_id
        where a.attribute_id = pAttribute_id
        limit 1
    );
END