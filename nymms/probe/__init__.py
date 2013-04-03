import time
import logging

from nymms.queue import QueueWorker
from nymms.resources import MonitoringGroup, Node, Monitor, Command

logger = logging.getLogger(__name__)


class Probe(QueueWorker):
    def run(self, max_sleep=2, min_sleep=1):
        did_task = False
        max_sleep = sleep = float(max_sleep)
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

    def task_handler(self, task):
        logger.debug("Handling task: %s" % (task.task))
        group_objects = []
        node_name = task.task['name']
        monitoring_groups = task.task['monitoring_groups']
        for group in monitoring_groups:
            try:
                group_objects.append(MonitoringGroup.registry[group])
            except KeyError:
                logger.warning("Monitoring group '%s' not found in registry "
                        "for node '%s'. Skipping." % (group, node_name))
                continue
        node = Node.registry.get(node_name,
                Node(node_name, monitoring_groups=group_objects))
        logger.debug("Executing monitors for node %s:" % (node_name))
        logger.debug(node.execute_monitors())
        return True

    def handle_task_result(self, task, result):
        if result:
            logger.debug("Deleting task: %s" % (task.task))
            task.delete()


