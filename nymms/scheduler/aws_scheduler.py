import logging
import time
import json

from boto.sqs.message import Message

from nymms import resources
from nymms.config import config
from nymms.tasks import Task
from nymms.scheduler.Scheduler import Scheduler

logger = logging.getLogger(__name__)


class AWSScheduler(Scheduler):
    def __init__(self, node_backend, conn_mgr, task_queue):
        self._node_backend = node_backend
        self._conn = conn_mgr
        self._queue_name = task_queue
        self._queue = None
        logger.debug(self.__class__.__name__ + " initialized.")

    def _setup_queue(self):
        if self._queue:
            return
        logger.debug("setting up queue %s", self._queue_name)
        self._queue = self._conn.sqs.create_queue(self._queue_name)

    def submit_task(self, task, **kwargs):
        self._setup_queue()
        logger.debug("Sending task '%s' to queue '%s'.", task.id,
                     self._queue_name)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return self._queue.write(m)
