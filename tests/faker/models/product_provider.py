# coding=utf-8
import logging
import random
import string
from datetime import datetime

import faker.providers

from catalog import utils
from catalog.models import (
    db,
    Product,
    ProductVariant,
    SellableProduct,
    SellableProductBundle,
    SellableProductSubSku,
    Attachment,
    VariantImage,
    EditingStatus, SellingStatus,
    SellableProductSeoInfoTerminal,
    Terminal,
    ProductLog, VariantAttribute, Attribute, AttributeOption, SellableProductBarcode)
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class ProductProvider(faker.providers.BaseProvider):
    """
    Cung cấp dữ liệu liên quan đến sản phẩm
    """

    def _get_uom_attr_option(self, variant_id):
        attribute_id = db.session.query(Attribute.id).filter(Attribute.code == 'uom').first()
        attribute_value = db.session.query(VariantAttribute.value).filter(VariantAttribute.variant_id == variant_id,
                                                                          VariantAttribute.attribute_id == attribute_id.id
                                                                          ).first()
        if not attribute_value:
            return None
        return AttributeOption.query.get(int(attribute_value.value))

    def _get_uom_attr_option_by_code(self, code):
        attribute_id = db.session.query(Attribute.id).filter(Attribute.code == 'uom').first()
        return AttributeOption.query.filter(
            AttributeOption.code == code,
            AttributeOption.attribute_id == attribute_id.id
        ).first()

    def product(self, brand_id=None, unit_id=None, master_category_id=None,
                attribute_set_id=None, objective_code=None, category_id=None, model=None,
                spu=None, name=None, created_by=None, editing_status_code=None, is_bundle=None, unit_po_id=None,
                is_seo=True):
        category = fake.category(is_active=True)
        ret = Product()
        ret.name = name or fake.text()
        ret.short_name = fake.text()
        ret.spu = fake.text() if spu is None else spu
        ret.brand_id = brand_id or fake.brand().id
        ret.unit_id = unit_id or fake.unit().id
        ret.unit_po_id = unit_po_id or fake.unit().id
        ret.master_category_id = master_category_id or fake.master_category(is_active=True).id
        ret.category_id = category_id or category.id
        ret.created_by = created_by or fake.iam_user(seller_id=category.seller_id).email
        ret.attribute_set_id = attribute_set_id or fake.attribute_set().id
        ret.warranty_months = fake.integer()
        ret.warranty_note = fake.text(50)
        ret.editing_status_code = editing_status_code or fake.random_element(('draft', 'approved'))
        ret.is_bundle = is_bundle or False
        ret.model = model
        if is_seo:
            ret.display_name = fake.text()
            ret.url_key = fake.text()
            ret.meta_title = fake.text()
            ret.meta_keyword = fake.text()
            ret.meta_description = fake.text()

        db.session.add(ret)
        db.session.commit()

        return ret

    def product_variant(self, product_id=None, created_by=None, editing_status_code=None, name=None,
                        uom_attr=None, uom_option_value=None, uom_ratio_attr=None, uom_ratio_value=None,
                        attribute_set_id=None):
        ret = ProductVariant()
        ret.name = name or fake.text()
        ret.url_key = utils.slugify(ret.name)
        ret.code = fake.text()
        ret.updated_at = datetime.now()
        ret.created_at = datetime.now()
        ret.product_id = product_id or fake.product(attribute_set_id=attribute_set_id).id
        ret.created_by = created_by if created_by else fake.user().email
        ret.editing_status_code = editing_status_code or fake.random_element(('draft', 'approved'))
        db.session.add(ret)
        db.session.flush()

        if not uom_attr:
            # create uom
            uom_attr = fake.uom_attribute(attribute_set_id=ret.product.attribute_set_id)
        uom_variant_attr = VariantAttribute()
        uom_variant_attr.variant_id = ret.id
        uom_variant_attr.attribute_id = uom_attr.id
        if not uom_option_value:
            if len(uom_attr.options) > 0:
                uom_variant_attr.value = random.choice(uom_attr.options).id
            else:
                fake_option = fake.attribute_option(attribute_id=uom_attr.id)
                uom_variant_attr.value = fake_option.id
        else:
            uom_variant_attr.value = uom_option_value

        if uom_ratio_value:
            if not uom_ratio_attr:
                uom_ratio_attr = fake.uom_ratio_attribute(attribute_set_id=ret.product.attribute_set_id)

            uom_ratio_variant_attr = VariantAttribute()
            uom_ratio_variant_attr.variant_id = ret.id
            uom_ratio_variant_attr.attribute_id = uom_ratio_attr.id
            uom_ratio_variant_attr.value = uom_ratio_value
            db.session.add(uom_ratio_variant_attr)

        db.session.add(uom_variant_attr)
        self.uom_attr = uom_variant_attr
        db.session.commit()

        ret.uom_id = uom_attr.id
        return ret

    def product_variant_images(self, variant_id=None):
        ret = VariantImage(
            url=fake.text(),
            label=fake.text(),
            priority=fake.random_int(1, 10),
            is_displayed=fake.boolean(),
            product_variant_id=variant_id
        )
        db.session.add(ret)
        db.session.commit()
        return ret

    def product_variant_only(self, product_id=None, created_by=None, editing_status_code=None, name=None):
        ret = ProductVariant()
        ret.name = name or fake.text()
        ret.url_key = utils.slugify(ret.name)
        ret.code = fake.text()
        ret.updated_at = datetime.now()
        ret.created_at = datetime.now()
        ret.product_id = product_id or fake.product().id
        ret.created_by = created_by if created_by else fake.user().email
        ret.editing_status_code = editing_status_code or fake.random_element(('draft', 'approved'))
        db.session.add(ret)
        db.session.flush()

        return ret

    def product_variant_attribute(self, product_variant_id, attribute_id, value):
        variant_attr = VariantAttribute()
        variant_attr.variant_id = product_variant_id
        variant_attr.attribute_id = attribute_id
        variant_attr.value = value
        db.session.add(variant_attr)
        db.session.flush()

    def sellable_product(self, variant_id=None, sku=None, category_id=None,
                         brand_id=None, attribute_set_id=None, seller_id=None,
                         selling_status_code=None, barcode=None,
                         editing_status_code=None, description=None,
                         is_bundle=None, detailed_description=None,
                         provider_id=None, unit_id=None, unit_po_id=None,
                         master_category_id=None, uom_code=None, uom_ratio=None, seller_sku=None,
                         created_by=None, updated_by=None, tracking_type=None,
                         expiry_tracking=None, expiration_type=None, days_before_exp_lock=None, terminal_id=None,
                         model=None, is_seo=True):
        ret = SellableProduct()
        ret.name = fake.name()
        ret.variant_id = variant_id or self.product_variant(attribute_set_id=attribute_set_id).id
        ret.barcode = barcode or utils.random_string(length=20)
        ret.sku = sku or ''.join(random.choice(string.digits) for _ in range(12))
        ret.seller_sku = seller_sku or ''.join(random.choice(string.digits) for _ in range(12))
        ret.seller_id = seller_id or fake.seller().id
        ret.unit_id = unit_id or fake.unit().id
        ret.unit_po_id = unit_po_id or fake.unit().id
        ret.label = fake.text()
        ret.editing_status_code = editing_status_code or \
                                  fake.random_element(('draft', 'approved'))
        ret.selling_status_code = selling_status_code or \
                                  random.choice(['hang_ban', 'hang_trung_bay'])
        ret.is_bundle = random.choice((True, False)) if is_bundle is None else is_bundle
        ret.allow_selling_without_stock = random.choice((True, False))
        ret.tracking_type = tracking_type if tracking_type is not None else random.choice((True, False))
        ret.expiry_tracking = expiry_tracking
        if ret.expiry_tracking:
            ret.expiration_type = expiration_type if expiration_type is not None else random.choice((1, 2))
            ret.days_before_exp_lock = days_before_exp_lock if days_before_exp_lock is not None else random.choice(
                (1, 2))
        ret.provider_id = provider_id or fake.seller_prov().id
        ret.master_category_id = master_category_id or fake.master_category(is_active=True).id
        ret.uom_ratio = uom_ratio
        ret.created_by = created_by or fake.text()
        ret.updated_by = updated_by or fake.text()
        ret.model = model
        if not uom_code:
            attr_option = self._get_uom_attr_option(ret.variant_id)
        else:
            attr_option = self._get_uom_attr_option_by_code(uom_code)
        if attr_option:
            ret.uom_name = attr_option.value
            ret.uom_code = attr_option.code
        else:
            ret.uom_code = uom_code

        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            product = variant.product
            ret.product_id = product.id
            ret.brand_id = product.brand_id
            ret.category_id = product.category_id
            ret.attribute_set_id = variant.product.attribute_set_id
            ret.tax_in_code = product.tax_in_code
            ret.tax_out_code = product.tax_out_code
            ret.warranty_months = product.warranty_months
            ret.warranty_note = product.warranty_note
            ret.name = product.name
            if product.model:
                ret.model = product.model
        else:
            variant = ProductVariant.query.get(ret.variant_id)
            product = variant.product
            ret.product_id = product.id
            ret.brand_id = brand_id or fake.brand().id
            ret.category_id = category_id or fake.category(is_active=True).id
            ret.attribute_set_id = variant.product.attribute_set_id
            ret.tax_in_code = fake.text(length=10)
            ret.tax_out_code = fake.text(length=10)
            ret.warranty_months = random.choice([0, 12, 24, 36])
            ret.warranty_note = fake.text()
            ret.name = fake.text()

        db.session.add(ret)
        db.session.flush()

        terminal = Terminal(
            code=fake.text(20),
            name=fake.name(),
            type=fake.text(20),
            platform=fake.text(30),
            full_address=fake.text(),
            seller_id=ret.seller_id,
            is_active=True
        )
        db.session.add(terminal)
        db.session.flush()

        terminal_id = terminal_id if terminal_id is not None else terminal.id
        if is_seo:
            seo = SellableProductSeoInfoTerminal(
                terminal_id=0,
                sellable_product_id=ret.id,
                short_description=fake.text(),
                description=fake.text(),
                terminal_code=0,
                created_by=fake.text(),
                updated_by=updated_by or fake.text()
            )
            db.session.add(seo)
            db.session.flush()
        return ret

    def sellable_product_barcode(self, sku_id=None, barcode=None, source=None, created_by=None, is_default=None):
        ret = SellableProductBarcode()
        ret.sellable_product_id = sku_id or self.sellable_product().id
        ret.barcode = barcode or utils.random_string(length=20)
        ret.source = source or utils.random_string(length=20)
        ret.created_by = created_by or utils.random_string(length=20)
        ret.is_default = is_default or random.choice([True, False])

        db.session.add(ret)
        db.session.flush()
        return ret

    def gen_sku(self):
        year = str(random.randint(0, 99)).zfill(2)
        month = str(random.randint(1, 12)).zfill(2)
        end = ''.join(random.sample('0123456789', 5))

        return year + month + end

    def attachment(self, sellable_product_id):
        attachment = Attachment()
        attachment.name = fake.unique_str()
        attachment.url = fake.unique_str()
        attachment.sellable_product_id = sellable_product_id

        db.session.add(attachment)
        db.session.flush()

        return attachment

    def variant_product_image(self, product_variant_id):
        image = VariantImage()
        image.name = fake.unique_str()
        image.url = fake.unique_str()
        image.label = fake.unique_str()
        image.is_displayed = fake.boolean()
        image.priority = fake.integer()
        image.product_variant_id = product_variant_id
        image.status = 1

        db.session.add(image)
        db.session.flush()

        return image

    def selling_status(self):
        return random.choice([
            'hang_ban',
            'hang_trung_bay',
            'hang_sap_het',
            'ngung_kinh_doanh',
            'hang_dat_truoc'
        ])

    def checking_status(self):
        return random.choice([
            'draft',
            'pending',
            'approved',
            'reject',
            'inactive'
        ])

    def init_editing_status(self):
        data = [{
            'name': 'Đang nhập liệu',
            'code': 'processing',
            'can_moved_status': 'pending_approval,inactive,suspend',
            'config': '{"color": "#FF7F2A"}'
        }, {
            'name': 'Chờ duyệt',
            'code': 'pending_approval',
            'can_moved_status': 'reject,active,suspend',
            'config': '{"color": "purple"}'
        }, {
            'name': 'Hiệu lực',
            'code': 'active',
            'can_moved_status': 'inactive,reject,suspend',
            'config': '{"color": "green"}'
        }, {
            'name': 'từ chối',
            'code': 'reject',
            'can_moved_status': 'processing,suspend',
            'config': '{"color": "#FF7F2A"}'
        }, {
            'name': 'Vô hiệu',
            'code': 'inactive',
            'can_moved_status': 'pending_approval,active,suspend',
            'config': '{"color": "#A5A5A5"}'
        }, {
            'name': 'Tạm ẩn hiển thị',
            'code': 'suspend',
            'can_moved_status': 'pending_approval,active,inactive,reject,processing',
            'config': '{"color": "pink"}'
        }, {
            'name': 'Duyet',
            'code': 'approved',
        }, {
            'name': 'Nhap',
            'code': 'draft',
        }]
        for item in data:
            status = EditingStatus(**item)
            db.session.add(status)
        db.session.commit()

    def status(self):
        return random.choice([
            'chờ xử lí',
            'bình thường',
            'bán hết bỏ mẫu',
            'ngừng kinh doanh'
        ])

    def bundle(self, sellable_product, bundle_items):
        sellable_product.is_bundle = True

        for priority, item in enumerate(bundle_items, 1):
            bundle_info = SellableProductBundle(
                bundle_id=sellable_product.id,
                sellable_product_id=item.id,
                priority=priority,
                quantity=fake.integer()
            )
            db.session.add(bundle_info)
        db.session.commit()

    def init_selling_status(self):
        data = [{
            'name': 'Hàng bán',
            'code': 'hang_ban',
            'config': '{"color": "#108ee9"}'
        }, {
            'name': 'Hàng sắp hết',
            'code': 'hang_sap_het',
            'config': '{"color": "#FF7F7F"}'
        }, {
            'name': 'Ngừng kinh doanh',
            'code': 'ngung_kinh_doanh',
            'config': '{"color": "#A5A5A5"}'
        }]
        for item in data:
            status = SellingStatus(**item)
            db.session.add(status)
        db.session.commit()

    def product_hisotry(self, sellableProduct):
        product_log = ProductLog(sku=sellableProduct.sku)
        product_log.updated_by = fake.email()
        product_log.old_data = fake.text()
        product_log.new_data = fake.text()
        product_log.updated_at = datetime.now()
        product_log.created_at = datetime.now()
        db.session.add(product_log)
        db.session.commit()
        return product_log

    def sub_sku(self, sellable_product, sub_sku=None):
        sub_sku = SellableProductSubSku(
            sellable_product_id=sellable_product.id,
            sub_sku=sub_sku or fake.text()

        )
        db.session.add(sub_sku)
        db.session.commit()
        return sub_sku
