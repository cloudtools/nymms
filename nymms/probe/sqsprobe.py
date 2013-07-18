import time
import logging
import json

from boto.sqs.message import Message

from nymms.resources import Monitor
from nymms.utils import commands

logger = logging.getLogger(__name__)

from nymms.config import config


class SQSProbe(object):
    def __init__(self, connection, queue_name):
        self.connection = connection
        self.queue_name = queue_name
        self.tasks_received = 0
        self.get_queue()

    def get_queue(self):
        while True:
            logger.debug("Attaching to queue '%s'." % (self.queue_name))
            self.queue = self.connection.get_queue(self.queue_name)
            if self.queue:
                logger.debug('Attached to queue.')
                break
            logger.debug('Unable to attach to queue.  Sleeping before retry.')
            time.sleep(2)

    def get_task(self, wait_time=config.settings['probe']['queue_wait_time'],
            timeout=config.settings['monitor_timeout'] + 3):
        if not self.queue:
            logger.debug('Not attached to queue.')
            self.get_queue()
        logger.debug("Getting task from queue '%s'" % (self.queue_name))
        task = self.queue.read(visibility_timeout=timeout,
                wait_time_seconds=wait_time)
        return task

    def resubmit_task(self, task, delay):
        task['_attempt'] += 1
        m = Message()
        m.set_body(json.dumps(task))
        return self.queue.write(m, delay_seconds=delay)

    def submit_result(self, result, task):
        logger.debug("Submitting '%s' result for task %s." % (result,
            task['_url']))
        return

    def handle_task(self, task, timeout=config.settings['monitor_timeout']):
        task_data = json.loads(task.get_body())
        attempt = task_data['_attempt']
        monitor_name = task_data['monitor']['name']
        monitor = Monitor.registry[task_data['monitor']['name']]
        logger.debug("Executing %s attempt %d: %s" % (
            task_data['_url'], task_data['_attempt'],
            monitor.format_command(task_data)))
        try:
            monitor.execute(task_data, timeout)
            result = "SUCCESS"
        except commands.CommandException, e:
            logger.debug(str(e))
            if attempt <= 3:
                result = "SOFT FAIL"
                logger.debug("Resubmitting task %s." % (task_data['_url'],))
                self.resubmit_task(task_data,
                        config.settings['probe']['retry_delay'])
            else:
                result = "HARD FAIL"
                logger.debug("Retry limit hit, not resubmitting.")
        self.submit_result(result, task_data)
        logger.debug('Deleting task.')

    def run(self):
        while True:
            if not self.tasks_received % 10:
                logger.info('Tasks received: %d' % (self.tasks_received))
            logger.debug("Queue depth: %d" % (self.queue.count()))
            task = self.get_task(
                    wait_time=config.settings['probe']['queue_wait_time'])
            if not task:
                logger.debug("Queue '%s' empty." % (self.queue_name))
                continue
            self.tasks_received += 1
            self.handle_task(task)
            task.delete()
