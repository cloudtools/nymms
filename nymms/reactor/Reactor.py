import logging
import glob
import os
import sys

from nymms.daemon import NymmsDaemon
from nymms.config import yaml_config
from nymms.utils import load_object_from_string, logutil
from nymms.exceptions import OutOfDateState

logger = logging.getLogger(__name__)


class Reactor(NymmsDaemon):
    def __init__(self):
        self.handlers = {}
        self.suppression_manager = None
        self.state_manager = None

        super(Reactor, self).__init__()

    def list_handler_configs(self, path):
        path = os.path.expanduser(path)
        configs = glob.glob(os.path.join(path, '*.conf'))
        configs += glob.glob(os.path.join(path, '*.yaml'))
        return configs

    def get_handler_name(self, filename):
        return os.path.basename(filename)[:-5]

    def load_handler(self, handler_name, config, **kwargs):
        enabled = config.pop('enabled', False)

        if not enabled:
            logger.debug("Handler %s 'enabled' is not set to true. "
                         "Skipping.", handler_name)
            return None
        cls_string = config.pop('handler_class')
        logger.debug('Initializing handler %s.', handler_name)
        try:
            handler_cls = load_object_from_string(cls_string)
            return handler_cls(config)
        except Exception:
            logutil.log_exception("Skipping handler %s due to "
                                  "unhandled exception:" % handler_name,
                                  logger)
            return None

    def load_handlers(self, handler_config_path, **kwargs):
        conf_files = self.list_handler_configs(handler_config_path)
        logger.info("Loading handlers from %s", handler_config_path)
        for f in conf_files:
            handler_name = self.get_handler_name(f)
            # We could eventually have the handlers get loaded everytime and
            # update them if their config has changed (via config_version
            # below).  For now lets not get that tricky.
            if handler_name in self.handlers:
                if not kwargs.get('force_load_handlers', False):
                    logger.debug("Handler %s already loaded, skipping.",
                                 handler_name)
                    continue
            _, config = yaml_config.load_config(f)
            handler = self.load_handler(handler_name, config, **kwargs)
            if handler:
                self.handlers[handler_name] = handler

        if not self.handlers:
            logger.error("No handlers loaded.  Exiting.")
            sys.exit(1)

    def get_result(self, **kwargs):
        raise NotImplementedError

    def get_state(self, task_id):
        return self.state_manager.get_state(task_id)

    def save_state(self, task_id, result, previous):
        return self.state_manager.save_state(task_id, result, previous)

    def is_suppressed(self, result):
        """Returns True if we should suppress the given result for event"""
        if not self.suppression_manager:
            logger.debug("is_suppressed(): No suppress backend, so returning "
                         "False")
            return False
        suppression_filter = self.suppression_manager.is_suppressed(result.id)
        if suppression_filter:
            suppression_filter.validate()
            logger.debug("Suppressed %s with '%s' (%s) created at %s",
                         result.id,
                         suppression_filter.regex,
                         suppression_filter.rowkey,
                         suppression_filter.created.isoformat())
        return suppression_filter

    def handle_result(self, result, **kwargs):
        previous_state = self.get_state(result.id)
        for handler_name, handler in self.handlers.iteritems():
            try:
                # We do suppression AFTER filters, so we have to
                # pass Reactor to the handler to do that for us
                handler.process(result, previous_state, self.is_suppressed)
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
        self.load_handlers(handler_config_path, **kwargs)
        while True:
            result = self.get_result(**kwargs)
            if not result:
                logger.debug('Result queue empty.')
                continue
            self.handle_result(result, **kwargs)
            self.delete_result(result)
