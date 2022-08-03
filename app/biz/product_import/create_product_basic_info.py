from catalog import celery, app
from catalog.api.imports.schema import ImportCreateProductBasicInfoParams
from catalog.biz.product_import.base import Importer
from catalog.biz.product_import.create_product import CreateProductTask
from catalog.extensions import convert_int_field
from catalog.extensions.exceptions import BadRequestException
from catalog.validators.attribute_set import ImportCreateProductBasicInfoValidator


class CreateProductBasicInfoImporter(Importer):
    def init_attributes(self):
        if not self.row.get('attribute set'):
            raise BadRequestException('Nhóm sản phẩm bỏ trống hoặc không chính xác.')
        self.attribute_set_id = convert_int_field(self.row.get('attribute set').split('=>').pop(0))

        ImportCreateProductBasicInfoParams().load(data={
            'attributeSetId': self.attribute_set_id
        })

        self.attribute_set = ImportCreateProductBasicInfoValidator.validate_attribute_set_id(self.attribute_set_id)
        self.attributes = ImportCreateProductBasicInfoValidator.validate_uom_attribute(
            self.attribute_set_id, attribute_set=self.attribute_set)

        self.specifications_attributes = self.attribute_set.get_specifications_attributes()


@celery.task(queue='import_product_basic_info')
def import_product_basic_info_task(params, environ=None, **kwargs):
    with app.request_context(environ):
        create_product_basic_info_task = CreateProductTask(
            file_id=params.get('id'),
            cls_importer=CreateProductBasicInfoImporter
        )
        create_product_basic_info_task.run()
