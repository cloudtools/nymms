import logging

from boto import sns
from boto import sqs
from boto.sqs.message import RawMessage

logger = logging.getLogger(__name__)


class SQSQueue(object):
    def __init__(self, connection, queue_name, visibility_timeout=30):
        if not isinstance(connection, sqs.connection.SQSConnection):
            raise TypeError("SQSQueue requires an SQSConnection object.")
        self.connection = connection
        self.queue_name = queue_name
        self.visibility_timeout = visibility_timeout
        self.create_queue()

    def create_queue(self):
        logger.debug("Initializing queue '%s'." % (self.queue_name))
        self.queue = self.connection.create_queue(self.queue_name,
                self.visibility_timeout)
        self.queue.set_message_class(RawMessage)

    def get(self):
        logger.debug("Querying for message on queue '%s'." % (self.queue_name))
        messages = self.queue.get_messages(attributes='All')
        if not messages:
            logger.debug("No message found on queue '%s'." % (self.queue_name))
            return None
        logger.debug('Message received.')
        return messages[0]


class SNSTopic(object):
    def __init__(self, connection, topic_name):
        if not isinstance(connection, sns.connection.SNSConnection):
            raise TypeError("SNSTopic requires an SNSConnection object.")
        self.connection = connection
        self.topic_name = topic_name
        self.create_topic()

    def create_topic(self):
        logger.debug("Creating SNS topic '%s'" % (self.topic_name))
        self.topic = self.connection.create_topic(self.topic_name)
        self.topic_arn = self.topic['CreateTopicResponse']\
                ['CreateTopicResult']['TopicArn']

    def subscribe(self, queue):
        logger.debug("Subscribing queue '%s' to topic '%s'." % (
                queue.queue.name, self.topic_name))
        return self.connection.subscribe_sqs_queue(self.topic_arn, queue.queue)

    def put(self, message):
        logger.debug("Submitting message to topic '%s'." % (self.topic_name))
        self.connection.publish(self.topic_arn, message)
