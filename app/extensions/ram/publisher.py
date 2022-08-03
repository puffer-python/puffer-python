import logging
import uuid

from library.pyram.factory.sender import SenderFactory
from catalog.extensions.ram.proto.dto_pb2 import AddVariantSkuMsg as _AddVariantSkuMsg

logger = logging.getLogger(__name__)

class Msg:
    def to_pb_msg(self):
        raise NotImplementedError

class AddVariantSkuMsg(Msg):
    def __init__(self, variant_sku, sibling_sku) -> None:
        self.variant_sku = variant_sku
        self.sibling_sku = sibling_sku

    def to_pb_msg(self):
        pb_msg = _AddVariantSkuMsg()
        pb_msg.variant_sku = self.variant_sku
        pb_msg.sibling_sku = self.sibling_sku

        return pb_msg


class RAMPublisher:
    def __init__(self, app=None) -> None:
        self.publisher = None
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, ram_kafka_bootstrap_server: str = 'localhost:9092'):
        if not app.config['RAM_KAFKA_ENABLE_ADD_VARIANT_SKU_PUBLISHER']:
            return
        try:
            self.publisher = SenderFactory.create_kafka_sender(
                conn_str=ram_kafka_bootstrap_server,
                message=_AddVariantSkuMsg
            )
        except Exception as e:
            logger.error(f'error when init RAM kafka publisher {ram_kafka_bootstrap_server}, msg {_AddVariantSkuMsg}: {e}')

    def publish(self, msg: Msg):
        if not self.publisher:
            return
        try:
            key = 'catalog_' + str(uuid.uuid4())
            self.publisher.publish(message=msg.to_pb_msg(), key=key)
        except Exception as e:
            logger.error(f'error when publish msg {msg}: {e}')


add_variant_sku_ram_publisher = RAMPublisher()
