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
    def __init__(self, reactor_name, conn_mgr, topic_name, alerters,
                 state_domain, queue_name=None):
        self.conn_mgr = conn_mgr
        self.state_domain = state_domain
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
        self.get_topic()
        self.get_queue()
        self.subscribe_queue_to_topic()
        self.get_domain()
        logger.debug("Reactor '%s' initialized.", reactor_name)

    def get_topic(self):
        logger.debug("Attaching to results topic '%s'.", self.topic_name)
        self.topic = self.conn_mgr.sns.create_topic(self.topic_name)
        response = self.topic['CreateTopicResponse']
        self.topic_arn = response['CreateTopicResult']['TopicArn']

    def get_queue(self):
        logger.debug("Attaching to queue '%s'.", self.queue_name)
        self.queue = self.conn_mgr.sqs.create_queue(self.queue_name)
        self.queue.set_message_class(RawMessage)

    def subscribe_queue_to_topic(self):
        logger.debug("Subscribing queue %s to topic %s.", self.queue_name,
                     self.topic_name)
        return self.conn_mgr.sns.subscribe_sqs_queue(self.topic_arn,
                                                     self.queue)

    def get_domain(self):
        domain = self.state_domain
        logger.debug("Getting state domain '%s' from SDB.", domain)
        self.domain = self.conn_mgr.sdb.create_domain(domain)

    def get_result(self):
        wait_time = self.reactor_config['queue_wait_time']
        timeout = self.reactor_config['visibility_timeout']
        logger.debug("Getting result from queue '%s'.", self.queue_name)
        result = self.queue.read(visibility_timeout=timeout,
                                 wait_time_seconds=wait_time)
        result_object = None
        if result:
            result_message = json.loads(result.get_body())['Message']
            result_dict = json.loads(result_message)
            result_object = results.Result.deserialize(result_dict,
                                                       origin=result)
            result_object.validate()
        return result_object

    def get_state(self, task):
        """ Gets the old state of the service from SDB. """
        state_item = self.domain.get_item(task.id, consistent_read=True)
        state = None
        if state_item:
            state = results.StateRecord.deserialize(state_item)
        return state

    def handle_result(self, task_result, timeout=None):
        msg_prefix = "%s result " % (task_result.id,)
        if not timeout:
            timeout = self.reactor_config.get('visibility_timeout', 30)
        previous = self.get_state(task_result)
        if task_result.state_type == results.HARD:
            logger.debug(msg_prefix + "current state_type is HARD. (%s)",
                         task_result.state_name)
            if not previous:
                logger.debug(msg_prefix + "has no previous state.")
                return self.notify(task_result)
            if previous.state_type == results.SOFT and \
                    task_result.state_type == results.HARD:
                logger.debug(msg_prefix + "previous state_type(%s) was SOFT, "
                             "current state_type(%s) is HARD.",
                             previous.state_name, task_result.state_name)
                return self.notify(task_result)
            if not (previous.state == task_result.state):
                logger.debug(msg_prefix + "previous state (%s) does not match "
                             "current state (%s).", previous.state_name,
                             task_result.state_name)
                return self.notify(task_result)

    def notify(self, task_result):
        logger.debug("%s result sent to notifiers.", task_result.id)
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
