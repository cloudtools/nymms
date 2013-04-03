import logging
import base64

from nymms.message import NanoMessage

logger = logging.getLogger(__name__)


class QueueWorker(object):
    def __init__(self, topic, queue):
        self.topic = topic
        self.queue = queue

        self.topic.subscribe(self.queue)

    def send_task(self, task_body):
        logger.debug("Sending task:")
        logger.debug("    %s" % (task_body))
        encoded = base64.b64encode(task_body)
        self.topic.put(encoded)

    def perform_task(self):
        task = self.get_task()
        if not task:
            return False
        result = self.task_handler(task)
        self.handle_task_result(task, result)
        # this just means we worked on a task, not that it was successful
        return True

    def get_task(self):
        logger.debug("Getting task from queue '%s'." % (self.queue.queue_name))
        message = self.queue.get()
        if not message:
            logger.debug("No task found.")
            return None
        logger.debug("Task received.")
        return NanoMessage(message)

    def task_handler(self, task):
        raise NotImplemented

    def handle_task_result(self, task, result):
        raise NotImplemented
