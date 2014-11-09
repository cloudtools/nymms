import logging
import collections

logger = logging.getLogger(__name__)

from schematics.types import BaseType

import arrow


class TimestampType(BaseType):
    def to_native(self, value, context=None):
        if isinstance(value, arrow.arrow.Arrow):
            return value
        return arrow.get(value)

    def to_primitive(self, value, context=None):
        return value.timestamp


StateObject = collections.namedtuple('StateObject', ['name', 'code'])
STATE_OK = StateObject('ok', 0)
STATE_WARNING = STATE_WARN = StateObject('warning', 1)
STATE_CRITICAL = STATE_CRIT = StateObject('critical', 2)
STATE_UNKNOWN = StateObject('unknown', 3)
STATES = collections.OrderedDict([
    ('ok', STATE_OK),
    ('warning', STATE_WARNING),
    ('critical', STATE_CRITICAL),
    ('unknown', STATE_UNKNOWN)])


class StateType(BaseType):
    def to_native(self, value, context=None):
        if isinstance(value, StateObject):
            return value
        try:
            int_value = int(value)
            try:
                return STATES.values()[int_value]
            except IndexError:
                return STATE_UNKNOWN
        except ValueError:
            return STATES[value.lower()]

    def to_primitive(self, value, context=None):
        return value.code


StateTypeObject = collections.namedtuple('StateTypeObject', ['name', 'code'])
STATE_TYPE_SOFT = StateTypeObject('soft', 0)
STATE_TYPE_HARD = StateTypeObject('hard', 1)
STATE_TYPES = collections.OrderedDict([
    ('soft', STATE_TYPE_SOFT),
    ('hard', STATE_TYPE_HARD)])


class StateTypeType(BaseType):
    def to_native(self, value, context=None):
        if isinstance(value, StateTypeObject):
            return value
        try:
            return STATE_TYPES.values()[int(value)]
        except ValueError:
            return STATE_TYPES[value.lower()]

    def to_primitive(self, value, context=None):
        return value.code
