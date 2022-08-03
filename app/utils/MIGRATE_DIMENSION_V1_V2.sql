SELECT DISTINCT s.sku
FROM sellable_products s, attributes af
WHERE EXISTS
    (SELECT va.id
     FROM variant_attribute va
     JOIN attributes a ON va.attribute_id = a.id
     WHERE s.variant_id = va.variant_id
       AND a.code = af.code
       AND value IS NOT NULL)
  AND (EXISTS
         (SELECT va.id
          FROM variant_attribute va
          JOIN attributes a ON va.attribute_id = a.id
          WHERE s.variant_id = va.variant_id
            AND a.code = concat('pack_', af.code)
            AND (value IS NULL
                 OR value = ''))
       OR NOT exists
         (SELECT va.id
          FROM variant_attribute va
          JOIN attributes a ON va.attribute_id = a.id
          WHERE s.variant_id = va.variant_id
            AND a.code = concat('pack_', af.code)
            AND value IS NOT NULL))
  AND af.code in ('weight',
                  'width',
                  'length',
                  'height')