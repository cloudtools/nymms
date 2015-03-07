import logging
import json

logger = logging.getLogger(__name__)

from boto.sqs.message import Message

from nymms.schemas import Task
from nymms.probe.Probe import Probe
from nymms.state.sdb_state import SDBStateManager
from nymms.utils.aws_helper import SNSTopic, ConnectionManager


class SQSProbe(Probe):
    def __init__(self, region, task_queue, results_topic, state_domain,
                 state_manager=SDBStateManager):
        self.region = region
        self.queue_name = task_queue
        self.topic_name = results_topic
        self.state_manager = state_manager(region, state_domain)

        self._conn = None
        self._queue = None
        self._topic = None

        super(SQSProbe, self).__init__()

    @property
    def conn(self):
        if not self._conn:
            self._conn = ConnectionManager(self.region)
        return self._conn

    @property
    def queue(self):
        if not self._queue:
            self._queue = self.conn.sqs.create_queue(self.queue_name)
        return self._queue

    @property
    def topic(self):
        if not self._topic:
            self._topic = SNSTopic(self.region, self.topic_name)
        return self._topic

    def get_task(self, **kwargs):
        wait_time = kwargs.get('queue_wait_time')
        timeout = kwargs.get('monitor_timeout') + 3
        logger.debug("Getting task from queue %s.", self.queue_name)
        task_item = self.queue.read(visibility_timeout=timeout,
                                    wait_time_seconds=wait_time)
        task = None
        if task_item:
            task = Task(json.loads(task_item.get_body()), origin=task_item)
        return task

    def resubmit_task(self, task, delay, **kwargs):
        task.increment_attempt()
        logger.debug("Resubmitting task %s with %d second delay.", task.id,
                     delay)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return self.queue.write(m, delay_seconds=delay)

    def submit_result(self, result, **kwargs):
        logger.debug("%s - submitting '%s/%s' result", result.id,
                     result.state.name, result.state_type.name)
        return self.topic.publish(json.dumps(result.to_primitive()))

    def delete_task(self, task):
        self.queue.delete_message(task._origin)
