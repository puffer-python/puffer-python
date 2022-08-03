# coding=utf-8
import flask
from flask_login import current_user
import sqlalchemy as sa
from flask import current_app

from catalog import (
    models,
    validators,
)
from catalog.extensions import exceptions as exc
from catalog.services.products import ProductQuery
from catalog.services.seller import get_default_platform_owner_of_seller


class ProductCommonValidator(validators.Validator):
    @staticmethod
    def validate_num_draft_product_in_progress(**kwargs):
        """
        Validate whether current user has too many products in draft mode.

        By default (i.e., via UI), users are permitted only one.If we receive
        internal API call from allowed internal services, just let them create
        as many products as they want. For details, please
        see ticket: https://jira.teko.vn/browse/CATALOGUE-145

        :param kwargs:
        :return:
        """
        if flask.request.host in current_app.config['INTERNAL_HOST_URLS']:
            return
        existed = models.Product.query.filter(
            models.Product.editing_status_code == 'draft',
            models.Product.created_by == current_user.email
        ).first()
        if existed:
            raise exc.BadRequestException(
                message=f'Bạn có 1 sản phẩm {existed.name} '
                        f'ở seller {existed.category.seller.name} đang trong quá trình tạo, '
                        'vui lòng hoàn thành tạo mới sản phẩm đó để tiếp tục',
            )

    @staticmethod
    def validate_unit(unit_id=None, unit_code=None, **kwargs):
        unit = {}
        if unit_id:
            unit = models.Unit.query.get(unit_id)
        elif unit_code:
            unit = models.Unit.query.filter(
                models.Unit.code == unit_code
            ).first()
        if unit is None:
            raise exc.BadRequestException('Đơn vị không tồn tại')

    @staticmethod
    def validate_category(category_id=None, category_code=None, **kwargs):
        if not any([category_id, category_code]):
            raise exc.BadRequestException('Vui lòng chọn Danh mục ngành hàng')

        seller_id = kwargs.get('seller_id') or current_user.seller_id
        category_seller_id = seller_id
        if kwargs.get('default_category'):
            default_platform_owner_id = get_default_platform_owner_of_seller(seller_id)
            category_seller_id = default_platform_owner_id

        if category_id:
            category = models.Category.query.filter(
                models.Category.id == category_id,
            ).first()
        else:
            category = models.Category.query.filter(
                models.Category.code == category_code,
                models.Category.seller_id == category_seller_id
            ).options(
                sa.orm.load_only('is_active', 'id')
            ).first()
        if not category:
            raise exc.BadRequestException(
                'Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại'
            )
        if not category.is_active:
            raise exc.BadRequestException(
                'Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại'
            )
        if not category.is_leaf:
            raise exc.BadRequestException(
                'Vui lòng chọn danh mục ngành hàng là nút lá'
            )

    @staticmethod
    def validate_categories(**kwargs):
        category_ids = kwargs.get('category_ids')
        if not category_ids:
            return
        if len(category_ids) != len(set(category_ids)):
            raise exc.BadRequestException('Một sản phẩm chỉ được thuộc 1 danh mục ngành hàng của 1 seller')

        categories = models.Category.query.filter(
            models.Category.id.in_(category_ids)
        ).all()

        if len(category_ids) != len(categories):
            raise exc.BadRequestException(
                'Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại'
            )
        seller_categories = {}
        for category in categories:
            if not category.is_active:
                raise exc.BadRequestException('Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại')
            if not category.is_leaf:
                raise exc.BadRequestException('Vui lòng chọn danh mục ngành hàng là nút lá')
            if seller_categories.get(category.seller_id):
                raise exc.BadRequestException('Một sản phẩm chỉ được thuộc 1 danh mục ngành hàng của 1 seller')
            seller_categories[category.seller_id] = True

    @staticmethod
    def validate_master_category_id(master_category_id=None, **kwargs):
        if master_category_id:
            master_category = models.MasterCategory.query.options(
                sa.orm.load_only('is_active', 'id')
            ).get(master_category_id)
            if not master_category:
                raise exc.BadRequestException(
                    'Danh mục sản phẩm không tồn tại trên hệ thống, vui lòng chọn lại'
                )
            if not master_category.is_active:
                raise exc.BadRequestException(
                    'Danh mục sản phẩm đang bị vô hiệu, vui lòng chọn lại'
                )
            if not master_category.is_leaf:
                raise exc.BadRequestException(
                    'Vui lòng chọn danh mục sản phẩm là nút lá'
                )

    @staticmethod
    def validate_brand(brand_id=None, brand_code=None, **kwargs):
        if not any([brand_id, brand_code]):
            raise exc.BadRequestException('Vui lòng bổ sung thông tin Thương hiệu')

        if brand_id:
            brand = models.Brand.query.options(
                sa.orm.load_only('is_active')
            ).get(brand_id)
        else:
            brand = models.Brand.query.filter(
                models.Brand.code == brand_code
            ).options(
                sa.orm.load_only('is_active')
            ).first()
        if not brand:
            raise exc.BadRequestException(
                'Thương hiệu không tồn tại, vui lòng chọn lại'
            )
        if not brand.is_active:
            raise exc.BadRequestException(
                'Thương hiệu đang bị vô hiệu, vui lòng chọn lại'
            )

    @staticmethod
    def validate_tax_in_code(tax_in_code=None, **kwargs):
        is_bundle = kwargs.get('is_bundle')
        if is_bundle and tax_in_code is not None:
            raise exc.BadRequestException(
                'Không nhập mã thuế vào đối với sản phẩm bundle'
            )
        if not is_bundle and not bool(tax_in_code):
            raise exc.BadRequestException('Vui lòng bổ sung Thuế mua vào')
        if tax_in_code:
            tax_in = models.Tax.query.filter(
                models.Tax.code == tax_in_code
            ).first()
            if not tax_in:
                raise exc.BadRequestException('Mã thuế vào không tồn tại')

    @staticmethod
    def validate_tax_out_code(tax_out_code=None, **kwargs):
        is_bundle = kwargs.get('is_bundle')
        if is_bundle and tax_out_code is not None:
            raise exc.BadRequestException(
                'Không nhập mã thuế ra đối với sản phẩm bundle'
            )

        if tax_out_code:
            tax_out = models.Tax.query.filter(
                models.Tax.code == tax_out_code
            ).first()
            if not tax_out:
                raise exc.BadRequestException('Mã thuế ra không tồn tại')

    @staticmethod
    def validate_attribute_set_id(attribute_set_id, **kwargs):
        attribute_set = models.AttributeSet.query.get(attribute_set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')

    @staticmethod
    def validate_type(type, **kwargs):
        exists = models.Misc.query.filter(
            models.Misc.type == 'product_type',
            models.Misc.code == type
        ).scalar() is not None
        if not exists:
            raise exc.BadRequestException('Không tồn tại mã loại hình sản phẩm')


class GetProductInfoValidator(validators.Validator):
    @staticmethod
    def validate_product_id(product_id, **kwargs):
        query = ProductQuery()
        query.apply_filters({'id': product_id})
        if len(query) == 0:
            raise exc.BadRequestException(
                f'Không tồn tại sản phẩm có id là {product_id}'
            )


class DeleteDraftProductValidator(validators.Validator):
    @staticmethod
    def validate_(email, **kwargs):
        query = ProductQuery().restrict_by_user(email).apply_filters({
            'editing_status_code': 'draft'
        })
        product = query.first()
        if not product:
            raise exc.BadRequestException('Bạn đang không có sản phẩm nháp')
        for variant in product.variants:
            if variant.sellable_products:
                raise exc.BadRequestException(
                    'Dữ liệu đang được sử dụng, bạn không thể xóa'
                )


class ProductCommonFromImportValidator(ProductCommonValidator):
    @staticmethod
    def validate_seller_id(**kwargs):
        return True

    @staticmethod
    def validate_num_draft_product_in_progress(**kwargs):
        pass


class ProductUpdateValidator(validators.Validator):
    @staticmethod
    def validate_is_draft(data, obj_id, **kwargs):
        product = models.Product.query.get(obj_id)

        if not product or product.created_by != current_user.email:
            raise exc.BadRequestException(f'Không tồn tại sản phẩm có id là {obj_id}')

        if product.editing_status_code != 'draft':
            raise exc.BadRequestException(
                "Sản phẩm không có trạng thái biên tập là đang nháp. Bạn không thể sửa thông tin")

    @staticmethod
    def validate_category(data, **kwargs):
        if 'category_id' in data:
            ProductCommonValidator.validate_category(
                data['category_id'], **kwargs
            )

    @staticmethod
    def validate_master_category_id(data, **kwargs):
        ProductCommonValidator.validate_master_category_id(
            data.get('master_category_id'), **kwargs
        )

    @staticmethod
    def validate_brand(data, **kwargs):
        if 'brand_id' in data:
            ProductCommonValidator.validate_brand(
                data['brand_id'], **kwargs
            )

    @staticmethod
    def validate_tax(data, obj_id, **kwargs):
        tax_in_code = data.get('tax_in_code')
        tax_out_code = data.get('tax_out_code')
        product = models.Product.query.get(obj_id)

        if tax_in_code is not None:
            ProductCommonValidator.validate_tax_in_code(
                tax_in_code, **{'is_bundle': product.is_bundle, **kwargs}
            )

        if tax_out_code is not None:
            ProductCommonValidator.validate_tax_out_code(
                tax_out_code, **{'is_bundle': product.is_bundle, **kwargs}
            )

    @staticmethod
    def validate_type(data, **kwargs):
        if data.get('type'):
            ProductCommonValidator.validate_type(data.get('type'), **kwargs)
