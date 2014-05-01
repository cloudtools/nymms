import logging
import time

import nymms
from nymms.daemon import NymmsDaemon
from nymms.resources import Node
from nymms.tasks import Task
from nymms.scheduler.lock.SchedulerLock import NoOpLock

logger = logging.getLogger(__name__)


class Scheduler(NymmsDaemon):
    task_id_template = "{node[name]}:{monitor[name]}"

    def __init__(self, node_backend, lock=None):
        self._node_backend = node_backend
        if not lock:
            lock = NoOpLock()

        self._lock = lock
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
        interval = kwargs.get('interval')
        while True:
            start = time.time()
            if self._lock.acquire():
                self.run_once(**kwargs)
                run_time = time.time() - start
                logger.info("Scheduler iteration took %d seconds.", run_time)
                sleep_time = interval - max(run_time, 0)
                logger.info("Scheduler sleeping for %d seconds.", sleep_time)
            else:
                # Only sleep for 10 seconds before checking the lock again
                # when we don't acquire the lock. Allows for faster takeover.
                sleep_time = 10
                logger.info("Failed to acquire lock, sleeping for %d seconds.",
                            sleep_time)
            time.sleep(sleep_time)

    def run_once(self, **kwargs):
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

