import logging

logger = logging.getLogger(__name__)

import uuid
import time


class SchedulerLock(object):
    def __init__(self, duration, lock_name="scheduler_lock"):
        self.id = self.get_instance_id()
        self.duration = duration
        self.lock_name = lock_name
        logger.debug("%s:%s initialized with %s duration.",
                     self.__class__.__name__, self.id, duration)

    def get_instance_id(self):
        """ Can be overridden, but a random UUID at launch is probably good
        enough.
        """
        return uuid.uuid4().hex

    def lock_expired(self, expiry, now):
        """ Returns True if the lock is expired, False otherwise.  """
        if not expiry or int(now) > int(expiry):
            return True
        return False

    def acquire(self):
        """ Should be overridden and return True or False depending on whether
        it got the lock or not.
        """
        raise NotImplemented


class NoOpLock(SchedulerLock):
    def __init__(self):
        logger.warning("!!! Using NoOpLock")
        logger.warning("!!! Do not do this if you are planning to run more ")
        logger.warning("!!! than one scheduler.""")

    def acquire(self):
        return True
