import logging

logger = logging.getLogger(__name__)

from schematics.types import BaseType

import arrow


class TimestampType(BaseType):
    def to_native(self, value, context=None):
        if isinstance(value, arrow.arrow.Arrow):
            return value
        return arrow.get(value)

    def to_primitive(self, value, context):
        return value.timestamp
