import logging

logger = logging.getLogger(__name__)

from nymms.utils import load_object_from_string


class Handler(object):
    def __init__(self, config=None):
        self.config = config
        self._filters = []
        self._suppression_enabled = self.config.pop(
            'suppression_enabled',
            False)
        logger.debug("%s suppression enabled is %s",
                     self.__class__.__name__,
                     self._suppression_enabled)

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
        if not self._filters:
            return True
        results = {}
        for f in self._filters:
            try:
                results[f.__name__] = f(result, previous_state)
            except Exception as e:
                logger.exception("Filter %s on Handler %s had an unhandled "
                        "exception. Ignoring: %s",
                        f.__name__, self.__class__.__name__, e)
                continue
        logger.debug("Handler %s filter results: %s", self.__class__.__name__,
                    results)
        return all(results.values())

    def _process(self, result, previous_state, is_suppressed):
        """First checks to see if the given event should be filtered and
        then sees if it passes the suppressor (if enabled).  If pass, then
        call the subclass's process() method"""
        cname = self.__class__.__name__
        if self._filter(result, previous_state):
            if not self.suppression_enabled:
                logger.debug("Handler %s filters returned true for %s",
                        cname, result.id)
                return self.process(result, previous_state)
            elif self.suppression_enabled and not is_suppressed(result):
                logger.debug("Handler %s filters & suppressor returned true"
                        " for %s, reacting.", cname, result.id)
                return self.process(result, previous_state)
            else:
                logger.debug("Handler %s suppressor returned false"
                        " for %s, skipping.", cname, result.id)
        else:
            logger.debug("Handler %s filters returned false for %s, skipping.",
                    cname, result.id)

    def process(self, result, previous_state):
        """ Meant to be overridden by subclasses - should handle the actual
        process of reacting to a result.
        """
        raise NotImplementedError

    @property
    def suppression_enabled(self):
        """Are suppressions enabled for this handler?"""
        return self._suppression_enabled
