import logging
import json

logger = logging.getLogger(__name__)

from boto.sqs.message import Message

from nymms.tasks import Task
from nymms.probe.Probe import Probe
from nymms.state.sdb_state import SDBStateBackend
from nymms.utils.aws_helper import SNSTopic


class SQSProbe(Probe):
    def __init__(self, conn_mgr, task_queue, results_topic, state_domain,
                 state_backend=SDBStateBackend):
        self._conn = conn_mgr
        self._queue_name = task_queue
        self._topic_name = results_topic
        self._topic = None
        self._queue = None
        self._state_backend = state_backend(conn_mgr.sdb, state_domain)
        super(SQSProbe, self).__init__()

    def _setup_queue(self, **kwargs):
        if self._queue:
            return
        logger.debug("setting up queue %s", self._queue_name)
        self._queue = self._conn.sqs.create_queue(self._queue_name)

    def _setup_topic(self, **kwargs):
        if self._topic:
            return
        logger.debug("setting up topic %s", self._topic_name)
        self._topic = SNSTopic(self._conn, self._topic_name)

    def get_task(self, **kwargs):
        self._setup_queue(**kwargs)
        wait_time = kwargs.get('queue_wait_time')
        timeout = kwargs.get('monitor_timeout') + 3
        logger.debug("Getting task from queue %s.", self._queue_name)
        task_item = self._queue.read(visibility_timeout=timeout,
                                     wait_time_seconds=wait_time)
        task = None
        if task_item:
            task = Task.deserialize(json.loads(task_item.get_body()),
                                    origin=task_item)
        return task

    def resubmit_task(self, task, delay, **kwargs):
        self._setup_queue(**kwargs)
        task.increment_attempt()
        logger.debug("Resubmitting task %s with %d second delay.", task.id,
                     delay)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return self._queue.write(m, delay_seconds=delay)

    def submit_result(self, result, **kwargs):
        self._setup_topic()
        logger.debug("%s - submitting '%s/%s' result", result.id,
                     result.state_name, result.state_type_name)
        return self._topic.publish(json.dumps(result.serialize()))
