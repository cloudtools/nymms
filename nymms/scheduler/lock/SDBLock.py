import logging

logger = logging.getLogger(__name__)

import time

from boto.exception import SDBResponseError

from nymms.scheduler.lock.SchedulerLock import SchedulerLock


class SDBLock(SchedulerLock):
    def __init__(self, duration, conn, domain_name,
                 lock_name="scheduler_lock"):
        super(SDBLock, self).__init__(duration, lock_name)
        self.conn = conn
        self.domain_name = domain_name
        self.domain = None
        self.lock = None

    def setup_domain(self):
        if self.domain:
            return
        logger.debug("Setting up lock domain %s", self.domain_name)
        self.domain = self.conn.create_domain(self.domain_name)

    def acquire(self):
        logger.debug("Attempting to acquire lock %s:%s", self.domain_name,
                     self.lock_name)
        self.setup_domain()
        now = int(time.time())
        existing_lock = self.domain.get_item(self.lock_name,
                                              consistent_read=True)
        lock_body = {'expiry': now + self.duration,
                     'timestamp': now,
                     'owner': self.id}
        expected_value = ['timestamp', False]
        if existing_lock:
            logger.debug("Existing lock found: %s", existing_lock)
            existing_ts = existing_lock['timestamp']
            if not existing_lock['owner'] == self.id:
                if not self.lock_expired(existing_lock['expiry'], now):
                    logger.debug("Lock still valid, not taking over.")
                    return False
                else:
                    logger.info("Lock expired, attempting takeover.")
            else:
                logger.info("I already own the lock, updating.")
            expected_value = ['timestamp', existing_ts]

        try:
            self.domain.put_attributes(self.lock_name, lock_body,
                                        replace=bool(existing_lock),
                                        expected_value=expected_value)
            self.lock = lock_body
            logger.debug("Acquired lock %s:%s", self.domain_name,
                         self.lock_name)
            return True
        except SDBResponseError as e:
            if e.status == 409:
                logger.debug('Looks like someone else has acquired the lock.')
                return False
            raise
        return False
