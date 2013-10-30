import logging

logger = logging.getLogger(__name__)

from nymms.utils import load_object_from_string


class Handler(object):
    def __init__(self, config=None):
        self.config = config
        self._filters = []

    def _load_filters(self):
        filters = self.config.get('filters', [])
        if filters:
            for filter_string in filters:
                logging.debug("Adding Filter %s to Handler %s.", filter_string,
                              self.__class__.__name__)
                f = load_object_from_string(filter_string)
                self._filters.append(f)
        else:
            logger.debug("No filters configured for Handler %s.",
                         self.__class__.__name__)

    def _filter(self, result, previous_state):
        """ Runs the result & previous state through all the configured
        filters.  A filter should be a callable that accepts two arguments:
        the result and the previous state.  It should return either True or
        False regarding whether the message should be allowed through the
        handler.
        """
        if not self._filters:
            self._load_filters()
        # Assume that no filters means just that - that the result is
        # not to be filtered for the handler.
        results = [True]
        for f in self._filters:
            try:
                results.append(f(result, previous_state))
            except Exception as e:
                logger.exception("Filter %s on Handler %s had an unhandled "
                                 "exception. Ignoring:",
                                 f.__name__, self.__class__.__name__)
                continue
        return all(results)

    def _process(self, result, previous_state):
        if self._filter(result, previous_state):
            logger.debug("Handler %s filters returned true for %s, reacting.",
                         self.__class__.__name__, result.id)
            return self.process(result, previous_state)
        logger.debug("Handler %s filters returned false for %s, skipping.",
                     self.__class__.__name__, result.id)

    def process(self, result, previous_state):
        """ Meant to be overridden by subclasses - should handle the actual
        process of reacting to a result.
        """
        raise NotImplementedError
