import logging

logger = logging.getLogger(__name__)

import nymms

class NymmsDaemon(object):
    def __init__(self):
        logger.debug("%s initialized.", self.__class__.__name__)

    def main(self, *args, **kwargs):
        logger.debug("Launching %s version %s.", self.__class__.__name__,
                     nymms.__version__)
        self.run(*args, **kwargs)
                     
