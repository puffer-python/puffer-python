"""tbl misc update import_type list

Revision ID: fa7722e64c8f
Revises: b66024c1e267
Create Date: 2022-03-15 17:36:58.337145

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'fa7722e64c8f'
down_revision = 'b66024c1e267'
branch_labels = None
depends_on = None


def upgrade():
    # delete current import_type list except "upsert_product_category"
    op.execute('''
        DELETE FROM misc
        WHERE type = 'import_type' AND code <> 'upsert_product_category';
    ''')
    # create new import_type list
    op.execute('''
        INSERT INTO misc
            (name, `type`, code, config, `position`, id, created_at, updated_at)
        VALUES
            ('Đăng tải nhanh', 'import_type', 'create_product_quickly', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Đăng tải với thông tin cơ bản', 'import_type', 'create_product_basic_info', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Đăng tải với thông tin cơ bản và thuộc tính', 'import_type', 'create_product', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật trạng thái nhập liệu', 'import_type', 'update_editing_status', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thông tin cơ bản', 'import_type', 'update_product', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thuộc tính', 'import_type', 'update_attribute_product', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật ảnh sản phẩm', 'import_type', 'update_images_skus', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thông tin SEO', 'import_type', 'update_seo_info', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật tag của sản phẩm', 'import_type', 'tag_product', NULL, NULL, NULL, NOW(), NOW());
    ''')


def downgrade():
    # delete current import_type list except "upsert_product_category"
    op.execute('''
        DELETE FROM misc
        WHERE type = 'import_type' AND code <> 'upsert_product_category';
    ''')
    # create new import_type list
    op.execute('''
        INSERT INTO misc
            (name, `type`, code, config, `position`, id, created_at, updated_at)
        VALUES
            ('Đăng tải sản phẩm nhanh', 'import_type', 'create_product_quickly', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Đăng tải sản phẩm với thông tin cơ bản', 'import_type', 'create_product_basic_info', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Đăng tải sản phẩm với thông tin cơ bản và thuộc tính', 'import_type', 'create_product', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật trạng thái nhập liệu', 'import_type', 'update_editing_status', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thông tin cơ bản', 'import_type', 'update_product', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thuộc tính', 'import_type', 'update_attribute_product', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật ảnh sản phẩm', 'import_type', 'update_images_skus', '{"version"\:3}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật thông tin SEO', 'import_type', 'update_seo_info', '{"version"\:1}', NULL, NULL, NOW(), NOW()),
            ('Cập nhật tag của sản phẩm', 'import_type', 'tag_product', NULL, NULL, NULL, NOW(), NOW());
    ''')
