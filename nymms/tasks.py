import logging
import time

logger = logging.getLogger(__name__)

from nymms.data_types import NymmsDataType


class Task(NymmsDataType):
    def __init__(self, object_id, created=None, attempt=0, context=None,
                 origin=None):
        super(Task, self).__init__(object_id=object_id, origin=origin)
        self.attempt = attempt
        self.created = created
        self.context = context

    def validate_created(self):
        self.created = int(self.created or time.time())

    def validate_attempt(self):
        self.attempt = int(self.attempt or 0)

    def increment_attempt(self):
        self.attempt += 1
