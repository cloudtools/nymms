import unittest

from nymms.scheduler.lock.SchedulerLock import SchedulerLock

NOW = 1391115581.238759
DURATION = 30

class TestSchedulerLock(unittest.TestCase):
    def setUp(self):
        self.lock = SchedulerLock(DURATION)

    def test_lock_expired(self):
        no_lock = None
        self.assertIs(self.lock.lock_expired(no_lock, NOW), True)
        expired_lock = NOW - (DURATION + 5)
        self.assertIs(self.lock.lock_expired(expired_lock, NOW),
                          True)
        valid_lock = NOW + 5
        self.assertIs(self.lock.lock_expired(valid_lock, NOW), False)
