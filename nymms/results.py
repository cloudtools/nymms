import json
from nymms.exceptions import NymmsException

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


class ResultValidationError(NymmsException):
    def __init__(self, field, data):
        self.field = field
        self.data = data

    def __str__(self):
        return "Invalid data (%s) in field: %s" % (self.data, self.field,)


class RequiredField(NymmsException):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        return "Required field is blank: %s" % (self.field,)


class TaskResult(object):
    def __init__(self, task_url, status=None, state=None, output='',
                 task_data=None):
        self.task_url = task_url
        self.status = status
        self.state = state
        self.output = output
        self.task_data = task_data
        self._cleaned = {}

    def __str__(self):
        self.validate()
        return "TaskResult: %s" % (self.task_url,)

    def __repr__(self):
        return str(self.serialize())

    def validate(self):
        required_fields = ['status', 'state', 'task_data']
        for field in required_fields:
            if getattr(self, field) is None:
                raise RequiredField(field)
        self.validate_status()
        self.validate_state()

    def validate_status(self):
        if isinstance(self.status, basestring):
            try:
                self.status = statuses.index(self.status.lower())
            except ValueError:
                raise ResultValidationError('status', self.status)

    def validate_state(self):
        if isinstance(self.state, basestring):
            try:
                self.state = states.index(self.state.lower())
            except ValueError:
                raise ResultValidationError('state', self.state)

    @property
    def state_name(self):
        self.validate_state()
        return states[self.state]

    @property
    def status_name(self):
        self.validate_status()
        try:
            return statuses[self.status]
        except IndexError:
            return "unknown"

    def serialize(self):
        if self._cleaned:
            return self._cleaned

        self.validate()
        d = self.__dict__

        for key, value in d.iteritems():
            if not key.startswith('_'):
                self._cleaned[key] = value

        self._cleaned['state'] = self.state_name
        self._cleaned['status'] = self.status_name

        return self._cleaned


class ResultEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, TaskResult):
            return o.serialize()
        return json.JSONEncoder.default(self, o)
