import base64
import json
import Queue
import time
import logging

from boto import sns
from boto import sqs
from boto.sqs.message import Message, RawMessage

from nanomon.utils import yaml_includes
from nanomon.message import NanoMessage
from nanomon.queue import QueueWorker
from nanomon.queue.backends.sns_sqs import SQSQueue, SNSTopic

logger = logging.getLogger(__name__)


class YamlNodeBackend(object):
    def __init__(self, path):
        self.path = path

    def get_nodes(self):
        logger.debug("Loading node config from %s" % (self.path))
        return yaml_includes.load_config(self.path)


class Scheduler(QueueWorker):
    def __init__(self, node_backend, topic, queue):
        self.node_backend = node_backend
        super(Scheduler, self).__init__(topic, queue)

    def run(self, sleep=300):
        while True:
            start = time.time()
            sleep = float(sleep)
            nodes = self.node_backend.get_nodes()
            for node, settings in nodes.iteritems():
                task = json.dumps({node: settings})
                logger.debug("Sending task for node '%s'." % (node))
                self.send_task(task)
            real_sleep = sleep - (time.time() - start)
            if real_sleep <= 0:
                continue
            logger.debug("Sleeping for %.02f." % (real_sleep))
            time.sleep(real_sleep)


class TaskWorker(QueueWorker):
    def run(self, max_sleep=2, min_sleep=1):
        did_task = False
        max_sleep = float(max_sleep)
        sleep = float(max_sleep)
        while True:
            last_did_task = did_task
            did_task = self.perform_task()
            if not did_task:
                if not last_did_task:
                    sleep = sleep - 1
                if sleep <= 0:
                    sleep = min_sleep
                logger.debug("Sleeping for %.02f." % (sleep))
                time.sleep(sleep)
            else:
                sleep = max_sleep

    def handle_task_result(self, task, result):
        if result:
            logger.debug("Deleting task: %s" % (task.task))
            task.delete()

    def task_handler(self, task):
        logger.debug("Handling task: %s" % (task.task))
        return True
