import logging
import time
import json
import uuid

from boto.sqs.message import Message

from nymms import resources

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

    def task_url(self, task):
        url = "nymms://{address}/{monitor[name]}/"
        return url.format(**task) + "?timestamp=%f" % (time.time())

    def task_uuid(self, url):
        _uuid = uuid.uuid5(uuid.NAMESPACE_URL, url)
        logger.debug("Task %s uuid %s" % (url, _uuid))
        return _uuid

    def run(self):
        while True:
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
                    # Give task a unique UUID
                    url = self.task_url(task)
                    task['_url'] = url
                    task['_uuid'] = self.task_uuid(url).hex
                    task['_attempt'] = 0
                    self.send_task(task, pass_count * 5)
                    self.tasks_sent += 1
                pass_count += 1
            time.sleep(10)


class YamlNodeBackend(object):
    def __init__(self, path):
        self.path = path

    def load_nodes(self):
        logger.debug("Loading node config from %s" % (self.path))
        resources.load_nodes(self.path, reset=True)
