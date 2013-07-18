import json

# status constants
OK = 0
WARN = WARNING = 1
CRIT = CRITICAL = 2

# Anything over status 2 is unknown
statuses = ['ok', 'warning', 'critical', 'unknown']

# state constants
SOFT = 0
HARD = 1

states = ['soft', 'hard']

class InvalidStatus(Exception):
    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "%s" % (self.status)


class InvalidState(Exception):
    def __init__(self, state):
        self.state = state

    def __str__(self):
        return "%s" % (self.state)


class TaskResult(object):
    def __init__(self, task_url, status, state, data):
        self.task_url = task_url
        self.status = self.validate_status(status)
        self.state = self.validate_state(state)
        self.data = data
        self.cleaned = {}

    def __str__(self):
        return "TaskResult: %s" % (str(self.pretty_serialize()),)

    def __repr__(self):
        return self.serialize()

    def validate_status(self, status):
        if isinstance(status, basestring):
            try:
                status = statuses.index(status.lower())
            except ValueError:
                raise InvalidStatus(status)
        return status

    def validate_state(self, state):
        if isinstance(state, basestring):
            try:
                state = states.index(state.lower())
            except ValueError:
                raise InvalidState(state)
        return state

    def __setattr__(self, attr, value):
        if attr == 'status':
            value = self.validate_status(value)
        if attr == 'state':
            value = self.validate_state(value)
        return object.__setattr__(self, attr, value)

    @property
    def state_name(self):
        return states[self.state]

    @property
    def status_name(self):
        try:
            return statuses[self.status]
        except IndexError:
            return "unknown"

    def serialize(self):
        d = self.__dict__
        if self.cleaned:
            return self.cleaned

        for key, value in d.iteritems():
            if key == 'cleaned':
                continue
            if not key.startswith('__'):
                self.cleaned[key] = value

        return self.cleaned

    def pretty_serialize(self):
        d = self.serialize()
        d['state'] = self.state_name
        d['status'] = self.status_name
        return d


class ResultEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, TaskResult):
            return o.serialize()
        return json.JSONEncoder.default(self, o)
