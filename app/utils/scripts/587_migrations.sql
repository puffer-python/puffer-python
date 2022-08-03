-- Backup sellable_products
CREATE TABLE `sellable_products_bk_19052022`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `category_id` int(0),
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `sellable_products_bk_052022_category_id`(`category_id`) USING BTREE
);
INSERT INTO sellable_products_bk_19052022
SELECT id, category_id
FROM sellable_products;
-- TAKA seller_id=33
-- Need to get sellers sell on Taka to migrate data
update sellable_products s
    join categories sc on s.category_id = sc.id
    join categories c on c.code = sc.code and c.seller_id = 33
set s.category_id = c.id
where s.seller_id != 33;

-- Update nguoc lai id cho bang mapping master categories va categories, truoc do se chay script de insert code vao bang mapping
-- VNPAYSHOP SELLER_ID=2

update mapping_master_seller_cats mmc
set master_category_id = (
    select mc.id from master_categories mc where mmc.master_category_code = mc.code
),
    category_id        = (
        select c.id
        from categories c
        where mmc.category_code = c.code
    );

-- Cap nhat category cho sku co mapping cho cac seller ban  tren cho VNSHOP va con san VNSHOP la default platform
-- VNSHOP_PLATFORM_ID = 2
update sellable_products s
    join mapping_master_seller_cats mmc on s.master_category_id = mmc.master_category_id
set s.category_id = mmc.category_id
where s.seller_id != 2
  and s.seller_id IN (select ps.seller_id from platform_sellers ps where ps.platform_id = 2 and is_default = 1);

-- Export platform categories cho PPM
select s.sku, s.category_id, c.code category_code, s.seller_id, p.platform_id from sellable_products s
join categories c on s.category_id = c.id
join platform_sellers p on p.seller_id = s.seller_id
where p.is_owner = 1 order by s.seller_id, s.sku;

-- New PPM
select s.sku, s.category_id, c.code category_code, s.seller_id, p.platform_id from sellable_products s
join categories c on s.category_id = c.id
join platform_sellers p on p.seller_id = s.seller_id
where s.seller_id in (5,6,9,10,11,12,13,14,15,16,17,19,20,21,22,23,24,25,26,28,29,30,31,32,34,35,38,39,41,42,43,44,45,46,47,50,51,52,53,54,55,57,58,59,60,61,62,63,65,66,67,68,69,70,71,72,73,74,75,76,77,78,80,81,82,83,84,85,86,87,88,90,91,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,134,135,136,137,138,139,140,141,142,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,307,308,309,316,317,318,319,320,321,323,324,327,328,329,331,332,333,334,335,336,337,338,339,340,341) order by s.seller_id, s.sku;

-- Export platform categories cho SRM
select s.sku, s.category_id, c.code category_code, s.seller_id from sellable_products s
join categories c on s.category_id = c.id
where s.seller_id in (5,6,15,16,42,43) order by s.seller_id, s.sku;

-- Migrate to new table product_categories, use for all sellers, we must run it after other scripts
insert into product_categories(product_id, category_id, created_by)
select s.product_id, s.category_id, s.created_by
from sellable_products s 
join categories c on s.category_id = c.id and 
exists (select ps.id from platform_sellers ps where ps.seller_id = c.seller_id and ps.is_owner = 1)
and s.product_id is NOT NULL


-- Insert sku vnshop for platform Karavan
insert into product_categories(product_id, category_id, created_by)
select distinct s.sku, s.product_id, sc.id, s.created_by
from sellable_products s 
join categories c on s.category_id = c.id
    join categories sc on c.code = sc.code 
and s.product_id is NOT NULL and s.seller_id=2 and sc.seller_id = 232