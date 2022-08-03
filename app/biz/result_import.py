import json
import logging
import secrets
from flask_login import current_user
from catalog import celery
from catalog import models as m
from catalog import (
    app,
    utils,
)

logger = logging.getLogger(__name__)

static_column_convert = {
    # 'brand': lambda x: m.Brand.query.filter(m.Brand.name == x).options(load_only('id')).first().id,
    # 'category': lambda x: m.Category.query.filter(m.Category.code == x.split('=>')[0]).options(
    #     load_only('id')).first().id,
    # 'master category': lambda x: m.MasterCategory.query.filter(m.MasterCategory.code == x.split('=>')[0]).options(
    #     load_only('id')).first().id,
    # 'vendor tax': lambda x: m.Tax.query.filter(m.Tax.label == x).options(load_only('id')).first().id,
    # 'product type': lambda x: m.Misc.query.filter(m.Misc.type == 'product_type', m.Misc.name == x).options(
    #     load_only('id')).first().id,
    # 'allow selling without stock?': lambda x: True if 'Yes' else False,
    # 'is auto generated serial?': lambda x: True if 'Yes' else False,
    # 'is tracking serial?': lambda x: True if 'Yes' else False,
}


class ImportStatus:
    SUCCESS = 'success'
    FAILURE = 'failure'
    FATAL = 'fatal'


@celery.task(queue='result_import')
def capture_import_result(import_id, status, message, data, product_id, output, tag, environ):
    capture_import_result_task(import_id, status, message, data, product_id, output, tag, environ)


def capture_import_result_task(import_id, status, message, data, product_id, output, tag, environ):
    with app.request_context(environ):
        process = m.FileImport.query.get(import_id)
        saver = None
        if process.type in ('create_product', 'create_product_basic_info', 'create_product_quickly'):
            saver = CreateProductImportSaver(import_id, status, message, data, product_id, output, tag)

        if saver:
            saver.save()
        else:
            raise RuntimeError(f'Can not found saver for {process.type} import type')


class ImportCapture:
    def __init__(self, import_id, importer, result_import_id=None, tag=None):
        self.importer = importer
        self.data = self._series2dict(self.importer.row)
        self.output = {}
        self.message = ''
        self.status = None
        self.import_id = import_id
        self.tag = tag or secrets.token_hex(16)
        self.result_import_id = result_import_id
        self.product_id = None
        if importer.row.get('product_id'):
            self.product_id = importer.row.get('product_id')

    def _series2dict(self, row):
        return json.loads(row.to_json())

    def _call_job(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.status = ImportStatus.FATAL
            logger.fatal(exc)

        self._call_job()
        return self


class ImportSaverBase:
    def __init__(self, import_id, status, message, data, product_id, output, tag, id=None):
        self.import_id = import_id
        self.status = status
        self.message = message
        self.data = data
        self.output = output
        self.tag = tag
        self.product_id = product_id
        if id:
            self.record = m.ResultImport.query.get(id)
            self.record.status = self.status,
            self.record.message = self.message,
            self.record.data = self.data,
            self.record.output = self.output,
            self.record.updated_by = current_user.email,
            self.record.tag = self.tag,
            self.record.import_id = self.import_id,
            self.record.product_id = self.product_id
        else:
            self.record = m.ResultImport(
                status=self.status,
                message=self.message,
                data=self.data,
                output=self.output,
                updated_by=current_user.email,
                tag=self.tag,
                import_id=self.import_id,
                product_id=self.product_id
            )

    def normalize(self):
        pass

    def save(self):
        self.normalize()
        m.db.session.add(self.record)
        m.db.session.commit()


class CreateProductImportCapture(ImportCapture):
    def __init__(self, attribute_set_id, parent_row=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_row = parent_row
        self.attribute_set_id = attribute_set_id

    def _call_job(self):
        self.data = self._series2dict(self.importer.row)
        if hasattr(self.importer, 'attribute_set_str') and self.importer.attribute_set_str:
            self.data['attribute set'] = self.importer.attribute_set_str
        if self.parent_row is not None:
            parent = self._series2dict(self.parent_row)
            self._merge_parent_into_child(self.data, parent)

        capture_import_result.delay(
            self.import_id,
            self.status,
            self.message,
            self.data,
            self.product_id,
            self.output,
            self.tag,
            utils.environ2json()
        )

    def _merge_parent_into_child(self, child, parent):
        for k, v in child.items():
            if not v:
                child[k] = parent.get(k)


class CreateProductImportSaver(ImportSaverBase):
    def _map_static_column(self, data):
        for k, cvt_fn in static_column_convert.items():
            v = data.get(k)
            if v:
                try:
                    data[k] = cvt_fn(v)
                except AttributeError as e:
                    logger.exception(e)
                    logger.warning('Can not map %s, occurs error %s' % (k, str(e)))
        return data

    def _map_dynamic_column(self, data):
        keys = list(data.keys())

        # records: [(attribute code, option id)]
        records = m.AttributeOption.query.join(
            m.Attribute,
            m.AttributeOption.attribute_id == m.Attribute.id
        ).filter(
            m.Attribute.code.in_(keys),
            m.AttributeOption.value.in_(data.values())
        ).with_entities(
            m.Attribute.code,
            m.AttributeOption.id,
        ).all()
        data.update(records)

        return data

    def normalize(self):
        return
        # convert value of static column
        data = self._map_static_column(self.data)

        # convert value of dynamic column
        self.data = self._map_dynamic_column(data)
