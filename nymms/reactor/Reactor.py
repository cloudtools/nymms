import logging
import glob
import os
import sys

import nymms
from nymms.daemon import NymmsDaemon
from nymms.config import yaml_config
from nymms.utils import load_object_from_string, logutil
from nymms.exceptions import OutOfDateState

logger = logging.getLogger(__name__)


class Reactor(NymmsDaemon):
    def __init__(self):
        self._handlers = {}
        super(Reactor, self).__init__()

    def _load_handlers(self, handler_config_path, **kwargs):
        base_path = os.path.expanduser(handler_config_path)
        conf_files = glob.glob(os.path.join(base_path, '*.conf'))
        logger.debug("Loading handlers from %s", handler_config_path)
        for f in conf_files:
            handler_name = os.path.split(f)[1][:-5]
            # We could eventually have the handlers get loaded everytime and
            # update them if their config has changed (via config_version
            # below).  For now lets not get that tricky.
            if handler_name in self._handlers:
                if not kwargs.get('force_load_handlers', False):
                    logger.debug("Handler %s already loaded, skipping.",
                                 handler_name)
                    continue
            conf_version, conf = yaml_config.load_config(f)
            enabled = conf.pop('enabled', False)
            if not enabled:
                logger.debug("Handler %s 'enabled' is not set to true. "
                             "Skipping.", handler_name)
                continue
            cls_string = conf.pop('handler_class')
            logger.debug('Initializing handler %s.', handler_name)
            try:
                handler_cls = load_object_from_string(cls_string)
                self._handlers[handler_name] = handler_cls(conf)
            except Exception as e:
                logutil.log_exception("Skipping handler %s due to "
                    "unhandled exception:" % (handler_name), logger)
                continue

        if not self._handlers:
            logger.error("No handlers loaded.  Exiting.")
            sys.exit(1)

    def get_result(self, **kwargs):
        raise NotImplementedError

    # TODO: This calls on _state_backend but setting up of the _state_backend
    #       needs to be handled in the subclass.  Not sure how I should handle
    #       this, but I really like the idea of these being base class
    #       methods since in reality all reactors should have some sort of
    #       state backend, even if its a no-op
    def get_state(self, task_id):
        return self._state_backend.get_state(task_id)

    def save_state(self, task_id, result, previous):
        return self._state_backend.save_state(task_id, result, previous)

    def handle_result(self, result, **kwargs):
        previous_state = self.get_state(result.id)
        for handler_name, handler in self._handlers.iteritems():
            try:
                handler._process(result, previous_state)
            except Exception:
                logutil.log_exception("Unhandled %s handler "
                                      "exception:" % (handler_name,), logger)
                continue
        try:
            self.save_state(result.id, result, previous_state)
        except OutOfDateState:
            pass

    def run(self, handler_config_path, **kwargs):
        """ This will run in a tight loop. It is expected that the subclass's
        get_result() method will introduce a delay if the results queue is
        empty.
        """
        self._load_handlers(handler_config_path, **kwargs)
        while True:
            result = self.get_result(**kwargs)
            if not result:
                logger.debug('Result queue empty.')
                continue
            self.handle_result(result, **kwargs)
            result.delete()
