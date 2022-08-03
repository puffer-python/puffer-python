from typing import Callable, Dict, List, Tuple, Type
import logging
import time

from google.protobuf.message import Message

from catalog.extensions.ram.proto.dto_pb2 import UpdateSkuDimensionsWeightMsg
from catalog.services.products.sellable import get_by_sku as get_sellable_by_sku
from catalog.services.products.variant import variant_svc
from catalog.services.attributes.attribute import attribute_svc
from catalog.constants import DIMENSION_ATTRIBUTES_CODES


logger = logging.getLogger(__name__)


class RAMHandler:
    def __init__(
        self,
        proto_message: Type[Message],
        handler: Callable[[str, str, Message], List[Tuple[str, str, int, str, Message]]]
    ) -> None:
        self.proto_message = proto_message
        self.handler = handler
        self.retry_handler = _build_retry_handler(handler)

def _build_retry_handler(handler):
    def retry_handler(retry_tag, key, message: Message):
        logger.info(f'handler retried: tag {retry_tag}, msg key {key}, msg {message.DESCRIPTOR.full_name}')
        handler(key, message)

    return retry_handler


class HandlerRegistry:
    def __init__(self) -> None:
        self.handlers: Dict[str, RAMHandler] = {}
    
    def register(self, handler: RAMHandler):
        self.handlers[handler.proto_message.DESCRIPTOR.full_name] = handler


def update_sku_dimensions_weight(key, message: UpdateSkuDimensionsWeightMsg):
    logger.info(f'START consume msg update sku dimensions, weight: key {key}, msg {message}')
    start = time.time()
    sku = message.sku
    try:
        sellable = get_sellable_by_sku(sku=sku, only_fields=('variant_id'))
        if not sellable:
            logger.warning(f'sku {sku} not found when update dimensions, weight {message}')
            return

        dimension_attrs = attribute_svc.get_attribute_list(
            filters={'codes': DIMENSION_ATTRIBUTES_CODES},
            page_size=len(DIMENSION_ATTRIBUTES_CODES),
        )
        attrs = []
        for attr in dimension_attrs:
            if attr.code == 'length' and message.length > 0:
                attrs.append({'id': attr.id, 'value': message.length})
            if attr.code == 'width' and message.width > 0:
                attrs.append({'id': attr.id, 'value': message.width})
            if attr.code == 'height' and message.height > 0:
                attrs.append({'id': attr.id, 'value': message.height})
            if attr.code == 'weight' and message.weight > 0:
                attrs.append({'id': attr.id, 'value': message.weight})

        variant_svc.create_bulk_variant_attributes(
            {
                'variants': [
                    {'id': sellable.variant_id, 'attributes': attrs}
                ]
            },
            created_by='WMS' # warehouse management service
        )
        logger.info(f'SUCCESS consume msg update sku dimensions, weight: key {key}, msg {message},\
            AFTER {round(time.time() - start, 3)}s')
    except Exception as e:
        logger.error(f'ERROR when consume msg update sku dimensions, weight: key {key}, msg {message}: {e}')
    return []


handler_registry = HandlerRegistry()
handler_registry.register(RAMHandler(UpdateSkuDimensionsWeightMsg, update_sku_dimensions_weight))
