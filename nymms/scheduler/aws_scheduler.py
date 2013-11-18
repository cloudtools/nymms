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

    def _set_expiration(self, queue, expiration):
        if expiration:
            logger.debug("Setting queue %s message retention to %d.",
                         queue.name, expiration)
            queue.set_attribute('MessageRetentionPeriod',
                                expiration)

    def _setup_realm(self, realm, **kwargs):
        if realm in self._realm_queues:
            return
        queue_name = self._queue_name + '_REALM_' + realm
        logger.debug("setting up realm queue %s", queue_name)
        queue = self._conn.sqs.create_queue(queue_name)
        self._set_expiration(queue, kwargs.get('task_expiration', None))
        self._realm_queues[realm] = queue

    def _setup_queue(self, **kwargs):
        if self._default_queue:
            return
        logger.debug("setting up queue %s", self._queue_name)
        queue = self._conn.sqs.create_queue(self._queue_name)
        self._set_expiration(queue, kwargs.get('task_expiration', None))
        self._default_queue = queue

    def _choose_queue(self, task, **kwargs):
        realm = task.context['realm']
        if realm:
            self._setup_realm(realm, **kwargs)
            queue = self._realm_queues[realm]
        else:
            self._setup_queue(**kwargs)
            queue = self._default_queue
        return queue

    def submit_task(self, task, **kwargs):
        queue = self._choose_queue(task, **kwargs)
        logger.debug("Sending task '%s' to queue '%s'.", task.id,
                     queue.name)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return queue.write(m)
