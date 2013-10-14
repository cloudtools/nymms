import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)

from nymms.reactor.handlers.Handler import Handler


class LogHandler(Handler):
    """ A basic handler to send alerts to a log file via python's logging
    module.
    """
    def _setup_logger(self):
        if getattr(self, '_file_logger', None):
            return
        filename = self.config['filename']
        when = self.config['when']
        interval = self.config['interval']
        backup_count = self.config['backup_count']
        handler = TimedRotatingFileHandler(filename, when, interval,
                                           backup_count)
        handler.setLevel(logging.INFO)
        msg_fmt = '[%(asctime)s] %(message)s'
        handler.setFormatter(logging.Formatter(msg_fmt))
        self._file_logger = logging.getLogger('LogHandler')
        self._file_logger.propagate = False
        self._file_logger.addHandler(handler)
        self._file_logger.setLevel(logging.INFO)

    def process(self, result, previous_state):
        self._setup_logger()
        self._file_logger.info(result.serialize())
