import argparse
import logging
import sys
import time

logger = logging.getLogger(__name__)

from nymms.utils import logutil


def setup_logging(verbose=False):
    level = logutil.INFO
    if verbose:
        level = logutil.DEBUG
    if not verbose > 1:
        logutil.quiet_boto_logging()
    return logutil.setup_root_logger(stdout=level)


def parse_time(time_string, reference_time=int(time.time())):
    """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhd] and returns
    epoch time

    reference_time should be the epoch time used for calculating
    the time when using +XXXX[smhd]

    if time_string == 0, returns None"""
    if time_string == '0':
        return None

    if time_string[0] == '+' or time_string[0] == '-':
        last_char = time_string[len(time_string) - 1]
        user_value = time_string[0:(len(time_string) - 1)]
        if last_char == 's':
            epoch = reference_time + int(user_value)
        elif last_char == 'm':
            epoch = reference_time + (int(user_value) * 60)
        elif last_char == 'h':
            epoch = reference_time + (int(user_value) * 60 * 60)
        elif last_char == 'd':
            epoch = reference_time + (int(user_value) * 60 * 60 * 24)
        else:
            sys.stderr.write("Invalid time format: %s.  " +
                    "Missing s/m/h/d qualifier\n", time_string)
            exit(-1)
    else:
        epoch = int(time.strftime("%s",
            time.strptime(time_string, "%Y%m%d%H%M%S")))

    return epoch


class NymmsCommandArgs(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(NymmsCommandArgs, self).__init__(*args, **kwargs)
        self.add_argument('-v', '--verbose', action='count', default=0)
        self.add_argument('-c', '--config', default='/etc/nymms/config.yaml')
