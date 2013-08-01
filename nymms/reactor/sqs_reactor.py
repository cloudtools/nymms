import uuid
import logging
import json

logger = logging.getLogger(__name__)

from nymms import results
from nymms.config import config
from boto.sqs.message import RawMessage

# Used so people don't mess up the config
reserved_reactor_names = ['defaults']


class ReactorConfig(dict):
    def __missing__(self, key):
        return config.settings['reactors']['defaults'][key]


class InvalidReactorName(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Reactor name '%s' is invalid.  Must not be one of: %s" % (
                ', '.join(reserved_reactor_names))


class SQSReactor(object):
    def __init__(self, reactor_name, sqs_conn, sns_conn, topic_name, alerters,
            queue_name=None):
        self.sqs_conn = sqs_conn
        self.sns_conn = sns_conn
        self.topic_name = topic_name
        self.alerters = alerters
        self.queue_name = queue_name

        if reactor_name in reserved_reactor_names:
            raise InvalidReactorName(reactor_name)

        self.reactor_name = reactor_name
        self.reactor_config = ReactorConfig(
            config.settings['reactors'][reactor_name])
        if not queue_name:
            self.queue_name = "%s-%s" % (topic_name, uuid.uuid4().hex)
        self.create_channel()
        logger.debug("Reactor '%s' initialized." % (reactor_name,))

    def create_channel(self):
        logger.debug("Creating topic '%s'." % (self.topic_name,))
        self.topic = self.sns_conn.create_topic(self.topic_name)
        logger.debug("Creating queue '%s'." % (self.queue_name,))
        self.queue = self.sqs_conn.create_queue(self.queue_name)
        self.queue.set_message_class(RawMessage)
        self.topic_arn = self.topic['CreateTopicResponse']\
                ['CreateTopicResult']['TopicArn']
        logger.debug("Subscribing queue to topic.")
        return self.sns_conn.subscribe_sqs_queue(self.topic_arn, self.queue)

    def get_result(self):
        if not getattr(self, 'queue'):
            logger.debug('Not attached to queue.')
            self.create_channel()
        wait_time = self.reactor_config['queue_wait_time']
        timeout = self.reactor_config['visibility_timeout']
        logger.debug("Getting result from queue '%s'." % (self.queue_name,))
        result = self.queue.read(visibility_timeout=timeout,
                                 wait_time_seconds=wait_time)
        return result

    def handle_result(self, task_result, timeout=None):
        if not timeout:
            timeout = self.reactor_config.get('visibility_timeout', 30)
        body = json.loads(task_result.get_body())['Message']
        task_result = results.TaskResult(**json.loads(body))
        task_result.validate()
        logger.debug("%s: %s/%s" % (task_result.task['_id'],
                                    task_result.state,
                                    task_result.status))
        if task_result.state == results.HARD and \
                task_result.status > results.OK:
            self.notify(task_result)
        logger.debug(task_result.serialize())

    def notify(self, task_result):
        for alerter in self.alerters:
            alerter.alert(task_result)

    def run(self):
        while True:
            result = self.get_result()
            if not result:
                logger.debug("Result queue '%s' is empty." % (
                    self.queue_name,))
                continue
            self.handle_result(result)
            result.delete()
