# coding=utf-8
import logging


__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class RAM_QUEUE:
    RAM_DEFAULT_PARENT_KEY = 'default'
    RAM_INSERT_CATEGORY_KEY = 'catalog.category.insert'
    RAM_UPDATE_CATEGORY_KEY = 'catalog.category.update'
    RAM_INSERT_BRAND_KEY = 'catalog.brand.insert'
    RAM_UPDATE_BRAND_KEY = 'catalog.brand.update'
    RAM_INSERT_UNIT_KEY = 'catalog.unit.insert'
    RAM_UPDATE_UNIT_KEY = 'catalog.unit.update'


class ATTRIBUTE_TYPE:
    SELECTION = 'selection'
    MULTIPLE_SELECT = 'multiple_select'
    NUMBER = 'number'
    TEXT = 'text'

