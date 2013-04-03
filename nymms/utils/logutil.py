import logging
from logging.handlers import SysLogHandler
import os.path
import sys
import traceback


def quiet_boto_logging():
    """
    Boto's debug logs are full dumps of the XML that was passed between the
    client and server.  This can be annoying.  This is a simple function to
    hide those dumps whenever you put your code into debug.
    """
    logging.getLogger('boto').setLevel(logging.CRITICAL)


def setup_logging(tag_name=None, verbose=False, stdout=False, syslog=True,
        priority=SysLogHandler.LOG_LOCAL7):
    """
    Sets up a standard config for logging things to syslog, optionally
    logging to stdout as well.  If no tag_name is given, then the tag will
    be set to the name of the script being executed.

    Returns a logger.
    """
    if not tag_name:
        tag_name = os.path.basename(sys.argv[0])
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    log_level = logging.INFO
    base_format = (tag_name + ": %(filename)s.%(funcName)s %(levelname)s "
            "%(message)s")
    if verbose:
        log_level = logging.DEBUG
    if syslog:
        syslog_handler = SysLogHandler('/dev/log', priority)
        syslog_handler.setFormatter(logging.Formatter(base_format))
        syslog_handler.setLevel(log_level)
        logger.addHandler(syslog)
    if stdout:
        stdout_handler = logging.StreamHandler()
        stdout_format = "[%(asctime)s] " + base_format
        stdout_handler.setFormatter(logging.Formatter(stdout_format))
        stdout_handler.setLevel(log_level)
        logger.addHandler(stdout_handler)
    return logger


def log_exception(message=None, logger=logging):
    """
    Used to produce more cleanly readable exceptions in syslog by breaking
    the exception up over multiple logging calls.
    """
    if message:
        logger.error(message)
    logger.error('Exception output: ')
    exc_msg = traceback.format_exc().split('\n')
    for line in exc_msg:
        logger.error('    %s' % (line,))
