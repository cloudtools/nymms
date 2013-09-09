import logging

logger = logging.getLogger(__name__)


class Handler(object):
    def __init__(self, config=None):
        self.config = config

    def filter(self, result, previous_state):
        """ Used to determine whether a result should be reacted to or not.
        Should return True if it should be reacted to, False if not.
        Meant to be overridden by subclasses, or else always returns True.
        """
        return True

    def _process(self, result, previous_state):
        if self.filter(result, previous_state):
            logger.debug("Filter returned true for %s, reacting.", result.id)
            return self.process(result, previous_state)
        logger.debug("Filter returned false for %s, skipping.", result.id)

    def process(self, result, previous_state):
        """ Meant to be overridden by subclasses - should handle the actual
        process of reacting to a result.
        """
        raise NotImplementedError
