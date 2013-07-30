import logging
import time
import json

from boto.sqs.message import Message

from nymms import resources
from nymms.config import config

logger = logging.getLogger(__name__)


class SQSScheduler(object):
    def __init__(self, connection, queue_name, node_backend):
        self.node_backend = node_backend
        self.connection = connection
        self.queue_name = queue_name
        self.tasks_sent = 0
        self.create_queue()

    def create_queue(self):
        logger.debug("Creating queue '%s'." % (self.queue_name))
        self.queue = self.connection.create_queue(self.queue_name)

    def send_task(self, task, delay=None):
        logger.debug("Sending task to queue '%s'." % (self.queue_name))
        m = Message()
        m.set_body(json.dumps(task))
        return self.queue.write(m, delay_seconds=delay)

    def get_tasks(self):
        tasks = {}
        self.node_backend.load_nodes()
        nodes = resources.Node.registry
        for node_name, node in nodes.iteritems():
            tasks[node_name] = node.tasks
        return tasks

    def task_url(self, task, timestamp):
        url = "nymms://{address}/{monitor[name]}/"
        return url.format(**task) + "?timestamp=%f" % (timestamp,)

    def run(self):
        while True:
            start = time.time()
            logger.info("Tasks sent: %d" % (self.tasks_sent))
            pass_count = 0
            tasks = self.get_tasks()
            while True:
                working_index = tasks.keys()
                if not working_index:
                    break
                for node in working_index:
                    try:
                        task = tasks[node].pop()
                    except IndexError:
                        del(tasks[node])
                        continue
                    task_start = time.time()
                    url = self.task_url(task, task_start)
                    task['_url'] = url
                    task['_attempt'] = 0
                    task['_created'] = task_start
                    self.send_task(task)
                    self.tasks_sent += 1
                pass_count += 1
            run_time = time.time() - start
            logger.debug("Scheduler iteration took %d seconds." % (run_time,))
            sleep_time = (config.settings['scheduler']['interval'] -
                          max(run_time, 0))
            logger.debug("Scheduler sleeping for %d seconds." % (sleep_time,))
            time.sleep(sleep_time)


class YamlNodeBackend(object):
    def __init__(self, path):
        self.path = path

    def load_nodes(self):
        logger.debug("Loading node config from %s" % (self.path))
        resources.load_nodes(self.path, reset=True)
