import unittest

from nymms.schemas import Result, StateRecord, types
from nymms.reactor import filters


class TestFilters(unittest.TestCase):
    def setUp(self):
        self.result = Result({'id': 'test:filter',
                              'state': types.STATE_OK,
                              'state_type': types.STATE_TYPE_HARD})
        self.result.validate()
        self.record = StateRecord({
            'id': 'test:filter',
            'state': types.STATE_OK,
            'state_type': types.STATE_TYPE_HARD})
        self.record.validate()

    def test_hard_state(self):
        self.assertTrue(filters.hard_state(self.result, self.record))

        self.result.state_type = types.STATE_TYPE_SOFT
        self.result.validate()
        self.assertFalse(filters.hard_state(self.result, self.record))

    def test_ok_state(self):
        self.assertTrue(filters.ok_state(self.result, self.record))

        self.result.state = types.STATE_WARNING
        self.result.validate()
        self.assertFalse(filters.ok_state(self.result, self.record))

    def test_not_ok_state(self):
        self.assertFalse(filters.not_ok_state(self.result, self.record))

        self.result.state = types.STATE_WARNING
        self.result.validate()
        self.assertTrue(filters.not_ok_state(self.result, self.record))

    def test_warning_state(self):
        self.assertFalse(filters.warning_state(self.result, self.record))

        self.result.state = types.STATE_WARNING
        self.result.validate()
        self.assertTrue(filters.warning_state(self.result, self.record))

    def test_critical_state(self):
        self.assertFalse(filters.critical_state(self.result, self.record))

        self.result.state = types.STATE_CRITICAL
        self.result.validate()
        self.assertTrue(filters.critical_state(self.result, self.record))

    def test_unknown_state(self):
        self.assertFalse(filters.unknown_state(self.result, self.record))

        self.result.state = types.STATE_UNKNOWN
        self.result.validate()
        self.assertTrue(filters.unknown_state(self.result, self.record))

    def test_changed_state(self):
        f = filters.changed_state
        self.assertFalse(f(self.result, self.record))

        self.assertTrue(f(self.result, None))

        self.result.state = types.STATE_CRITICAL
        self.result.validate()
        self.assertTrue(f(self.result, self.record))

        self.result.state = types.STATE_OK
        self.result.state_type = types.STATE_TYPE_SOFT
        self.result.validate()
        self.assertTrue(f(self.result, self.record))
