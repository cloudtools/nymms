import time
import logging
import json

from boto.sqs.message import Message

from nymms.resources import Monitor
from nymms.utils import commands

logger = logging.getLogger(__name__)

from nymms.config import config


class SQSProbe(object):
    def __init__(self, sqs_conn, sns_conn, queue_name, results_topic):
        self.sqs_conn = sqs_conn
        self.sns_conn = sns_conn
        self.queue_name = queue_name
        self.results_topic = results_topic
        self.tasks_received = 0
        self.get_queue()
        self.get_topic()

    def get_queue(self):
        while True:
            logger.debug("Attaching to task queue '%s'." % (self.queue_name))
            self.queue = self.sqs_conn.get_queue(self.queue_name)
            if self.queue:
                logger.debug('Attached to task queue.')
                break
            logger.debug('Unable to attach to queue.  Sleeping before retry.')
            time.sleep(2)

    def get_topic(self):
        logger.debug("Attaching to results topic '%s'." % (
            self.results_topic,))
        self.topic = self.sns_conn.create_topic(self.results_topic)
        logger.debug("Attached to results topic '%s'." % (self.results_topic,))

    def get_task(self):
        if not getattr(self, 'queue'):
            logger.debug('Not attached to queue.')
            self.get_queue()
        wait_time = config.settings['probe']['queue_wait_time']
        timeout = config.settings['monitor_timeout'] + 3
        logger.debug("Getting task from queue '%s'" % (self.queue_name))
        task = self.queue.read(visibility_timeout=timeout,
                               wait_time_seconds=wait_time)
        return task

    def resubmit_task(self, task, delay):
        task['_attempt'] += 1
        logger.debug("Resubmitting task %s with %d second delay." % (
            task['_url'], delay))
        m = Message()
        m.set_body(json.dumps(task))
        return self.queue.write(m, delay_seconds=delay)

    def submit_result(self, result, task):
        task_lifetime = 0
        if task.get('_created'):
            task_lifetime = time.time() - task['_created']
        logger.debug("Submitting '%s' result for task %s. (Attempt: %d, "
            "Total Time: %-.2f)" % (result, task['_url'], task['_attempt'],
                task_lifetime))
        return

    def handle_task(self, task):
        task_data = json.loads(task.get_body())
        timeout = config.settings['monitor_timeout']
        attempt = task_data['_attempt']
        task_created = task_data.get('_created')
        monitor = Monitor.registry[task_data['monitor']['name']]
        logger.debug("Executing %s attempt %d: %s" % (
            task_data['_url'], task_data['_attempt'],
            monitor.format_command(task_data)))
        task_start = time.time()
        task_in_flight_time = 0
        if task_created:
            task_in_flight_time = task_created - task_start
        try:
            stdout, stderr = monitor.execute(task_data, timeout)
            result = "SUCCESS"
        except commands.CommandException, e:
            task_run_time = time.time() - task_start
            logger.debug(str(e))
            if attempt <= config.settings['probe']['retry_attempts']:
                result = "SOFT FAIL"
                delay = max(config.settings['probe']['retry_delay'] -
                            task_run_time, 0)
                self.resubmit_task(task_data, delay)
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
            task = self.get_task()
            if not task:
                logger.debug("Queue '%s' empty." % (self.queue_name))
                continue
            self.tasks_received += 1
            self.handle_task(task)
            task.delete()
