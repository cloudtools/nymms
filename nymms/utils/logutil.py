import logging
from logging.handlers import SysLogHandler
import os.path
import sys
import traceback
import platform
import os

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

_pid = os.getpid()

syslog_socket_paths = {
    'Darwin': '/var/run/syslog',
    'Linux': '/dev/log'
}


def quiet_boto_logging():
    """
    Boto's debug logs are full dumps of the XML that was passed between the
    client and server.  This can be annoying.  This is a simple function to
    hide those dumps whenever you put your code into debug.
    """
    logging.getLogger('boto').setLevel(logging.CRITICAL)


def quiet_paramiko_logging():
    """ Paramiko is really noisy when set to INFO or below.

    This sets the paramiko logger to only send WARNING or above messages.
    """
    logging.getLogger('paramiko').setLevel(logging.WARNING)


def quiet_requests_connpool_logging():
    """ Paramiko is really noisy when set to INFO or below.

    This sets the paramiko logger to only send WARNING or above messages.
    """
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(
        logging.WARNING)


def get_syslog_path():
    system_os = platform.system()
    try:
        return syslog_socket_paths[system_os]
    except KeyError:
        raise ValueError("Unable to find syslog unix domain socket for os "
                         "'%s'." % (system_os))

DEFAULT_FORMAT = ('pid:' + str(_pid) + ' %(levelname)s %(name)s '
                  '%(module)s(%(funcName)s):%(lineno)d - %(message)s')


def setup_root_logger(stdout=INFO, filename=None, file_level=INFO,
                      file_mode='w', syslog=None,
                      syslog_facility=SysLogHandler.LOG_LOCAL7,
                      syslog_socket_path=None, syslog_tag=None,
                      time_format="%Y/%m/%d %H:%M:%S %Z",
                      message_format=DEFAULT_FORMAT):
    """Setup basic logging, including stdout, file, and syslog logging.

    Sets up the root logger, deleting any previously configured handlers.  It
    does this to make sure that we don't have multiples of the same handler
    being attached to the root logger, resulting in multiple messages of the
    same type.

    This should be called in the main script/command/daemon itself, and never
    inside libraries unless you really know what you're doing.

    :type stdout: int
    :param stdout: The logging level to send to stdout.  Can be any of the
        logging.* constants (logging.DEBUG, etc) or logutil constants
        (logutil.DEBUG, etc) which are just pointers to the logging constants.
        If set to None or False, disable stdout logging.
        Default: logging.INFO

    :type filename: string
    :param filename: The path to a file to log to.  Setting to None disables
        file logging.
        Default: None

    :type file_level: int
    :param file_level: The logging level to send to the file given in the
        'filename' parameter.  Can be any of the logging.* or logutil.*
        constants like the 'stdout' parameter.
        Default: logging.INFO

    :type file_mode: string
    :param file_mode: The mode to open the file at the 'filename' parameter
        with.
        Default: 'w'

    :type syslog: int
    :param syslog: The logging level to send to syslog.  Can be any of the
        logging.* or logutil.* constants.  Set to None to disable syslog
        logging.
        Default: None

    :type syslog_facility: int
    :param syslog_facility: The syslog facility to send messages to if syslog
        is enabled.  Can be any of the SysLogHandler.LOG_* facility constants.
        Default: SysLogHandler.LOG_LOCAL7

    :type syslog_socket_path: string
    :param syslog_socket_path: The path to the unix domain socket used by
        syslog if syslog is enabled.  If not given, will automatically try to
        determine the correct path.
        Default: None

    :type syslog_tag: string
    :param syslog_tag: The tag to be pre-pended to syslog messages.  If not
        given it will try to determine the name of the command that was
        called, and use that.
        Default: None

    :type time_format: string
    :param time_format: A time.strftime formatted string to use for the
        timestamp format.  This will be prepended to stdout and logfiles, but
        not to syslog (since syslog has it's own timestamp system)

    :type message_format: string
    :param message_format: A logging.Formatter formatted string to use for
        the output of log messages.  See the following for variables:
        http://docs.python.org/2/library/logging.html#logrecord-attributes
    """
    base_format = message_format
    timed_format = '[%(asctime)s] ' + base_format
    timed_formatter = logging.Formatter(timed_format, datefmt=time_format)
    logger = logging.getLogger()

    # Delete all previous handlers.
    for h in logger.handlers:
        logger.removeHandler(h)

    # Used to track what levels are being used by handlers.
    levels = []

    if stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(timed_formatter)
        stdout_handler.setLevel(stdout)
        levels.append(stdout)
        logger.addHandler(stdout_handler)

    if filename:
        file_handler = logging.FileHandler(filename, mode=file_mode)
        file_handler.setFormatter(timed_formatter)
        file_handler.setLevel(file_level)
        levels.append(file_level)
        logger.addHandler(file_handler)

    if syslog:
        if not syslog_socket_path:
            syslog_socket_path = get_syslog_path()
        syslog_handler = SysLogHandler(syslog_socket_path,
                                       facility=syslog_facility)
        if not syslog_tag:
            syslog_tag = os.path.basename(sys.argv[0])
        syslog_format = syslog_tag + ": " + base_format
        syslog_handler.setFormatter(logging.Formatter(syslog_format))
        syslog_handler.setLevel(syslog)
        levels.append(syslog)
        logger.addHandler(syslog_handler)

    # Set the logger level to the level of the lowest leveled handler
    logger.setLevel(min(levels))

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
