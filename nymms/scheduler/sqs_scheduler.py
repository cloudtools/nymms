import logging
import time
import json

from boto.sqs.message import Message

from nymms import resources
from nymms.config import config
from nymms.tasks import Task

logger = logging.getLogger(__name__)


class SQSScheduler(object):
    def __init__(self, conn_mgr, queue_name, node_backend):
        self.node_backend = node_backend
        self.conn_mgr = conn_mgr
        self.queue_name = queue_name
        self.tasks_sent = 0
        self.create_queue()

    def create_queue(self):
        logger.debug("Creating queue '%s'." % (self.queue_name))
        self.queue = self.conn_mgr.sqs.create_queue(self.queue_name)

    def send_task(self, task, delay=None):
        logger.debug("Sending task '%s' to queue '%s'." % (task.id,
                                                           self.queue_name))
        m = Message()
        m.set_body(json.dumps(task.serialize()))
        return self.queue.write(m, delay_seconds=delay)

    def get_tasks(self):
        tasks = {}
        self.node_backend.load_nodes()
        nodes = resources.Node.registry
        for node_name, node in nodes.iteritems():
            tasks[node_name] = node.monitors
        return tasks

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
                        task_context = tasks[node].pop()
                        task_id_template = "{node[name]}:{monitor[name]}"
                        task_id = task_id_template.format(**task_context)
                        task = Task(task_id, context=task_context)
                    except IndexError:
                        del(tasks[node])
                        continue
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
