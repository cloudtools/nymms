import argparse
import logging

logger = logging.getLogger(__name__)

from nymms.utils import logutil


def setup_logging(verbose=False):
    level = logutil.INFO
    if verbose:
        level = logutil.DEBUG
    if not verbose > 1:
        logutil.quiet_boto_logging()
    return logutil.setup_root_logger(stdout=level)


class NymmsDaemonCommand(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(NymmsDaemonCommand, self).__init__(*args, **kwargs)
        self.add_argument('-v', '--verbose', action='count', default=0)
        self.add_argument('-c', '--config', default='/etc/nymms/config.yaml')
