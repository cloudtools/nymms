import logging
import glob
import os
import sys

from nymms.config import yaml_config
from nymms.utils import load_class_from_name, logutil

logger = logging.getLogger(__name__)


class Reactor(object):
    def __init__(self):
        self._handlers = {}
        logger.debug(self.__class__.__name__ + " initialized.")

    def _load_handlers(self, handler_config_path, force=False):
        base_path = os.path.expanduser(handler_config_path)
        conf_files = glob.glob(os.path.join(base_path, '*.conf'))
        logger.debug("Loading handlers from %s", handler_config_path)
        for f in conf_files:
            handler_name = os.path.split(f)[1][:-5]
            if handler_name in self._handlers and not force:
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
            handler_cls = load_class_from_name(cls_string)
            self._handlers[handler_name] = handler_cls(conf)

        if not self._handlers:
            logger.error("No handlers loaded.  Exiting.")
            sys.exit(1)

    def get_result(self):
        raise NotImplementedError

    def get_state(self, task_id):
        raise NotImplementedError

    def handle_result(self, result):
        msg_prefix = "%s result" % (result.id,)
        previous_state = self.get_state(result.id)
        for handler_name, handler in self._handlers.iteritems():
            try:
                handler._process(result, previous_state)
            except Exception as e:
                logutil.log_exception("Unhandled %s handler "
                                      "exception:" % (handler_name,), logger)
                continue

    def run(self, handler_config_path):
        """ This will run in a tight loop. It is expected that the subclass's
        get_result() method will introduce a delay if the results queue is
        empty.
        """
        self._load_handlers(handler_config_path)
        while True:
            result = self.get_result()
            if not result:
                logger.debug('Result queue empty.')
                continue
            self.handle_result(result)
            result.delete()
