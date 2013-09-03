import json
import time
import logging

logger = logging.getLogger(__name__)

from nymms.data_types import NymmsDataType

# status constants
OK = 0
WARN = WARNING = 1
CRIT = CRITICAL = 2
UNKNOWN = 3

# Anything over status 2 is unknown
statuses = ['ok', 'warning', 'critical', 'unknown']

# state constants
SOFT = 0
HARD = 1

states = ['soft', 'hard']


def get_state_name(state_code):
    return states[state_code]


def get_status_name(status_code):
    if status_code > 3:
        return "unknown"
    return statuses[status_code]


def validate_status(status):
    if isinstance(status, basestring):
        try:
            return statuses.index(status.lower())
        except ValueError:
            raise ResultValidationError('status', status)
    elif isinstance(status, int):
        try:
            return statuses[status] and status
        except IndexError:
            raise ResultValidationError('status', status)
    raise ResultValidationError('status', status)


def validate_state(state):
    if isinstance(state, basestring):
        try:
            return states.index(state.lower())
        except ValueError:
            raise ResultValidationError('state', state)
    elif isinstance(state, int):
        try:
            return states[state] and state
        except IndexError:
            raise ResultValidationError('state', state)
    raise ResultValidationError('state', state)


class StateStatusMixin(object):
    def validate_status(self):
        self.status = validate_status(self.status)

    def validate_state(self):
        self.state = validate_state(self.state)

    def validate_timestamp(self):
        self.timestamp = int(self.timestamp or time.time())

    @property
    def state_name(self):
        self.validate_state()
        return get_state_name(self.state)

    @property
    def status_name(self):
        self.validate_status()
        return get_status_name(self.status)


class Result(NymmsDataType, StateStatusMixin):
    required_fields = ['state', 'status']

    def __init__(self, object_id, status=None, state=None, timestamp=None,
            output=None, task_context=None, result_object=None):
        super(Result, self).__init__(object_id)
        self.status = status
        self.state = state
        self.timestamp = timestamp
        self.output = output or ''
        self.task_context = task_context or {}
        self._result_object = result_object

    def delete(self):
        self._result_object.delete()

    def _serialize(self):
        self._cleaned['state_name'] = get_state_name(self.state)
        self._cleaned['status_name'] = get_status_name(self.status)

    @classmethod
    def deserialize(cls, data):
        result_message = json.loads(data.get_body())['Message']
        result_dict = json.loads(result_message)
        del(result_dict['state_name'])
        del(result_dict['status_name'])
        result_obj = super(Result, cls).deserialize(result_dict)
        result_obj._result_object = data
        return result_obj


class StateRecord(NymmsDataType, StateStatusMixin):
    required_fields = ['state', 'status']

    def __init__(self, object_id, timestamp=None, state=None, status=None):
        super(StateRecord, self).__init__(object_id)
        self.timestamp = timestamp
        self.state = state
        self.status = status
        self._cleaned = {}

    @classmethod
    def decode_value(cls, value):
        try:
           return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return str(value)

    @classmethod
    def deserialize(cls, sdb_item):
        record_id = sdb_item.pop('id')
        item_dict = {}
        for k, v in sdb_item.iteritems():
            item_dict[k] = cls.decode_value(v)
        return cls(record_id, **item_dict)
