import time
import logging
import json

logger = logging.getLogger(__name__)

from boto.sqs.message import Message

from nymms.resources import Monitor
from nymms.utils import commands
from nymms.config import config
from nymms import results


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
        response = self.topic['CreateTopicResponse']
        self.topic_arn = response['CreateTopicResult']['TopicArn']
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

    def submit_result(self, task_result):
        task_lifetime = 0
        task_data = task_result.task_data
        created = task_data.get('_created')
        if created:
            task_lifetime = time.time() - created
        task_data['_lifetime'] = task_lifetime
        logger.debug("Submitting '%s' result for task %s. (Attempt: %d, "
                     "Total Time: %-.2f)" % (task_result.status_name,
                                             task_data['_url'],
                                             task_data['_attempt'],
                                             task_lifetime))
        return self.sns_conn.publish(self.topic_arn,
                                     json.dumps(task_result.serialize()))

    def handle_task(self, task):
        task_data = json.loads(task.get_body())
        timeout = config.settings['monitor_timeout']
        attempt = task_data['_attempt']
        monitor = Monitor.registry[task_data['monitor']['name']]
        logger.debug("Executing %s attempt %d: %s" % (
            task_data['_url'], task_data['_attempt'],
            monitor.format_command(task_data)))
        task_start = time.time()
        task_result = results.TaskResult(task_data['_url'])
        task_result.task_data = task_data
        task_result.state = results.HARD
        try:
            output = monitor.execute(task_data, timeout)
            task_result.output = output
            task_result.status = results.OK
        except commands.CommandException, e:
            if isinstance(e, commands.CommandFailure):
                task_result.status = e.return_code
                task_result.output = e.output
            if isinstance(e, commands.CommandTimeout):
                task_result.status = results.UNKNOWN
            task_run_time = time.time() - task_start
            if attempt <= config.settings['probe']['retry_attempts']:
                task_result.state = results.SOFT
                delay = max(config.settings['probe']['retry_delay'] -
                            task_run_time, 0)
                self.resubmit_task(task_data, delay)
            else:
                logger.debug("Retry limit hit, not resubmitting.")
        self.submit_result(task_result)
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
