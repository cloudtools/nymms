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
        self._default_queue = None
        self._realm_queues = {}
        super(Scheduler, self).__init__()

    def _setup_realm(self, realm):
        if realm in self._realm_queues:
            return
        queue_name = self._queue_name + '_REALM_' + realm
        logger.debug("setting up realm queue %s", queue_name)
        self._realm_queues[realm] = self._conn.sqs.create_queue(queue_name)

    def _setup_queue(self):
        if self._default_queue:
            return
        logger.debug("setting up queue %s", self._queue_name)
        self._default_queue = self._conn.sqs.create_queue(self._queue_name)

    def _choose_queue(self, task):
        realm = task.context['realm']
        if realm:
            self._setup_realm(realm)
            queue = self._realm_queues[realm]
        else:
            self._setup_queue()
            queue = self._default_queue
        return queue

    def submit_task(self, task, **kwargs):
        queue = self._choose_queue(task)
        logger.debug("Sending task '%s' to queue '%s'.", task.id,
                     queue.name)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return queue.write(m)
