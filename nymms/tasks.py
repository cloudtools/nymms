import logging
import time

logger = logging.getLogger(__name__)

from nymms.data_types import NymmsDataType


class Task(NymmsDataType):
    def __init__(self, object_id, created=None, attempt=0, context=None,
                 origin=None):
        super(Task, self).__init__(object_id=object_id, origin=origin)
        self.attempt = attempt or 0
        self.created = created or time.time()
        self.context = context

    def validate_created(self):
        self.created = int(self.created)

    def validate_attempt(self):
        self.attempt = int(self.attempt)

    def increment_attempt(self):
        self.attempt += 1
