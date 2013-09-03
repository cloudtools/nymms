import logging
import time
import json

logger = logging.getLogger(__name__)

from nymms.data_types import NymmsDataType


class Task(NymmsDataType):
    def __init__(self, object_id, created=None, attempt=None, context=None,
                 task_object=None):
        super(Task, self).__init__(object_id)
        self.attempt = attempt
        self.created = created
        self.context = context
        self._task_object = task_object

    def validate_created(self):
        self.created = int(self.created or time.time())

    def validate_attempt(self):
        self.attempt = self.attempt or 0

    def increment_attempt(self):
        self.attempt += 1

    def delete(self):
        self._task_object.delete()

    @classmethod
    def deserialize(cls, data):
        message = json.loads(data.get_body())
        task_obj = super(Task, cls).deserialize(message)
        task_obj._task_object = data
        return task_obj
