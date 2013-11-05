import logging
import time

import nymms
from nymms.daemon import NymmsDaemon
from nymms.resources import Node
from nymms.tasks import Task

logger = logging.getLogger(__name__)


class Scheduler(NymmsDaemon):
    task_id_template = "{node[name]}:{monitor[name]}"

    def __init__(self, node_backend):
        self._node_backend = node_backend
        super(Scheduler, self).__init__()

    def get_tasks(self):
        tasks = {}
        self._node_backend._load_nodes()
        nodes = Node.registry
        for node_name, node in nodes.iteritems():
            tasks[node_name] = node.monitors
        return tasks

    def submit_task(self, task, **kwargs):
        raise NotImplementedError

    def run(self, **kwargs):
        while True:
            start = time.time()
            tasks = self.get_tasks()
            # This is done to make sure we submit one task per node until we've
            # submitted all the tasks.  This helps ensure we don't hammer a
            # single node with monitoring tasks
            while True:
                working_index = tasks.keys()
                if not working_index:
                    break
                for node in working_index:
                    try:
                        task_context = tasks[node].pop()
                        task_id = self.task_id_template.format(**task_context)
                        task = Task(task_id, context=task_context)
                    except IndexError:
                        del(tasks[node])
                        continue
                    self.submit_task(task, **kwargs)
            run_time = time.time() - start
            logger.debug("Scheduler iteration took %d seconds.", run_time)
            interval = kwargs.get('interval')
            sleep_time = interval - max(run_time, 0)
            logger.debug("Scheduler sleeping for %d seconds.", sleep_time)
            time.sleep(sleep_time)
