import logging

logger = logging.getLogger(__name__)

from nymms import defaults, results
from nymms.resources import Monitor
from nymms.utils import commands


class Probe(object):
    def __init__(self):
        logger.debug(self.__class__.__name__ + " initialized.")

    # TODO: This calls on _state_backend but setting up of the _state_backend
    #       needs to be handled in the subclass.  Not sure how I should handle
    #       this, but I really like the idea of these being base class
    #       methods since in reality all reactors should have some sort of
    #       state backend, even if its a no-op
    def get_state(self, task_id):
        return self._state_backend.get_state(task_id)

    def get_task(self, **kwargs):
        raise NotImplementedError

    def resubmit_task(self, task, delay):
        raise NotImplementedError

    def submit_result(self, result):
        raise NotImplementedError

    def handle_task(self, task, **kwargs):
        log_prefix = "%s - " % (task.id,)
        previous_state = self.get_state(task.id)
        # check if the timeout is defined on the task first, if not then
        # go with what was passed into handle_task via run, if all else fails
        # fall back to a reasonable timeout
        timeout = task.context.get('monitor_timeout',
                                   kwargs.get('monitor_timeout',
                                              defaults.MONITOR_TIMEOUT))
        max_retries = task.context.get('max_retries',
                                       kwargs.get('max_retries',
                                                  defaults.MAX_RETRIES))
        last_attempt = int(task.attempt)
        current_attempt = last_attempt + 1
        monitor = Monitor.registry[task.context['monitor']['name']]
        command = monitor.format_command(task.context)
        logger.debug(log_prefix + "attempt %d, executing: %s", current_attempt,
                     command)
        result = results.Result(task.id, timestamp=task.created,
                                task_context=task.context)
        result.state_type = results.HARD
        try:
            output = monitor.execute(task.context, timeout)
            result.output = output
            result.state = results.OK
        except commands.CommandException as e:
            if isinstance(e, commands.CommandFailure):
                result.state = e.return_code
                result.output = e.output
            if isinstance(e, commands.CommandTimeout):
                result.state = results.UNKNOWN
            if current_attempt <= max_retries:
                # XXX Hate this logic - hope to find a cleaner way to handle
                #     it someday.
                if (not previous_state or
                        previous_state.state_type == results.SOFT or
                        (previous_state.state_type == results.HARD and not
                            result.state == previous_state.state)):
                    logger.debug('Previous state_type is not hard and current '
                                 'state is different than previous state. '
                                 'Resubmitting task.')
                    result.state_type = results.SOFT
                    default_retry_delay = defaults.MONITOR_RETRY_DELAY
                    delay = task.context.get('retry_delay',
                                             kwargs.get('retry_delay',
                                                        default_retry_delay))
                    delay = max(delay, 0)
                    self.resubmit_task(task, delay)
            else:
                logger.debug("Retry limit hit, not resubmitting.")
        self.submit_result(result)

    def run(self, **kwargs):
        """ This will run in a tight loop. It is expected that the subclass's
        get_task() method will introduce a delay if the results queue is
        empty.
        """
        while True:
            task = self.get_task(**kwargs)
            if not task:
                logger.debug("Task queue is empty.")
                continue
            self.handle_task(task, **kwargs)
            task.delete()
