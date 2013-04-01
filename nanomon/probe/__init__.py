import time
import logging

from nanomon.queue import QueueWorker

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

    def handle_task_result(self, task, result):
        if result:
            logger.debug("Deleting task: %s" % (task.task))
            task.delete()

    def task_handler(self, task):
        logger.debug("Handling task: %s" % (task.task))
        return True
