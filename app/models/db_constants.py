from enum import Enum


class AttributeValueType(Enum):
    TEXT = 'text'
    NUMBER = 'number'
    SELECTION = 'selection'
    MULTI_SELECT = 'multiple_select'
