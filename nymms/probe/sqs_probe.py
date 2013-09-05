import time
import logging
import json

logger = logging.getLogger(__name__)

from boto.sqs.message import Message

from nymms.resources import Monitor
from nymms.utils import commands
from nymms.config import config
from nymms import results
from nymms.tasks import Task


class SQSProbe(object):
    def __init__(self, conn_mgr, queue_name, results_topic, state_domain):
        self.conn_mgr = conn_mgr
        self.queue_name = queue_name
        self.results_topic = results_topic
        self.state_domain = state_domain
        self.tasks_received = 0
        self.get_queue()
        self.get_topic()
        self.get_domain()

    def get_queue(self):
        while True:
            logger.debug("Attaching to task queue '%s'.", self.queue_name)
            self.queue = self.conn_mgr.sqs.get_queue(self.queue_name)
            if self.queue:
                logger.debug('Attached to task queue.')
                break
            logger.debug('Unable to attach to queue.  Sleeping before retry.')
            time.sleep(2)

    def get_topic(self):
        logger.debug("Attaching to results topic '%s'.", self.results_topic)
        self.topic = self.conn_mgr.sns.create_topic(self.results_topic)
        response = self.topic['CreateTopicResponse']
        self.topic_arn = response['CreateTopicResult']['TopicArn']
        logger.debug("Attached to results topic '%s'.", self.results_topic)

    def get_domain(self):
        domain = self.state_domain
        logger.debug("Getting state domain '%s' from SDB.", domain)
        self.domain = self.conn_mgr.sdb.create_domain(domain)

    def get_task(self):
        if not getattr(self, 'queue'):
            logger.debug('Not attached to queue.')
            self.get_queue()
        wait_time = config.settings['probe']['queue_wait_time']
        timeout = config.settings['monitor_timeout'] + 3
        logger.debug("Getting task from queue '%s'", self.queue_name)
        task_item = self.queue.read(visibility_timeout=timeout,
                                    wait_time_seconds=wait_time)
        task = None
        if task_item:
            task = Task.deserialize(json.loads(task_item.get_body()),
                                    origin=task_item)
        return task

    def get_state(self, task):
        """ Gets the old state of the service from SDB. """
        state_item = self.domain.get_item(task.id, consistent_read=True)
        state = None
        if state_item:
            state = results.StateRecord.deserialize(state_item)
        return state

    def resubmit_task(self, task, delay):
        task.increment_attempt()
        logger.debug("Resubmitting task %s with %d second delay.", task.id,
                     delay)
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return self.queue.write(m, delay_seconds=delay)

    def submit_result(self, task_result):
        logger.debug("Submitting '%s/%s' result for task %s.",
                     task_result.state_name, task_result.state_type_name,
                     task_result.id)

        return self.conn_mgr.sns.publish(self.topic_arn,
                                         json.dumps(task_result.serialize()))

    def handle_task(self, task):
        previous = self.get_state(task)
        timeout = config.settings['monitor_timeout']
        attempt = task.attempt
        max_retries = config.settings['probe']['retry_attempts']
        monitor = Monitor.registry[task.context['monitor']['name']]
        command = monitor.format_command(task.context)
        logger.debug("Executing %s attempt %d: %s", task.id, task.attempt,
                     command)
        task_start = time.time()
        task_result = results.Result(task.id, timestamp=task.created,
                                     task_context=task.context)
        task_result.state_type = results.HARD
        try:
            output = monitor.execute(task.context, timeout)
            task_result.output = output
            task_result.state = results.OK
        except commands.CommandException, e:
            if isinstance(e, commands.CommandFailure):
                task_result.state = e.return_code
                task_result.output = e.output
            if isinstance(e, commands.CommandTimeout):
                task_result.state = results.UNKNOWN
            task_run_time = time.time() - task_start
            if attempt <= max_retries:
                if not previous or previous.state_type == results.SOFT or (
                        previous.state_type == results.HARD and not
                        task_result.state == previous.state):
                    logger.debug('Previous state_type is not hard and current '
                                 'state is different than previous state. '
                                 'Resubmitting task.')
                    task_result.state_type = results.SOFT
                    delay = max(config.settings['probe']['retry_delay'] -
                                task_run_time, 0)
                    self.resubmit_task(task, delay)
            else:
                logger.debug("Retry limit hit, not resubmitting.")
        self.submit_result(task_result)

    def run(self):
        while True:
            if not self.tasks_received % 10:
                logger.info('Tasks received: %d', self.tasks_received)
            logger.debug("Queue depth: %d", self.queue.count())
            task = self.get_task()
            if not task:
                logger.debug("Queue '%s' empty.", self.queue_name)
                continue
            self.tasks_received += 1
            self.handle_task(task)
            task.delete()
