import unittest
import copy

from nymms.suppress.suppress import SuppressionManager
from nymms.schemas import Suppression

now = 0

SUPPRESSION_COMMON = {
    'ipaddr': '10.0.0.1', 'userid': 'testuser', 'comment': 'testcomment'}

SUPPRESSIONS = (
    {'rowkey': '4b068858-4e98-4028-8413-7cd9e4dd94d1',
     'regex': 'test_foo',
     'expires': now + 60},
    {'rowkey': '8a8fa3c8-29ee-4ad2-931a-57287c36b151',
     'regex': 'test_bar.*',
     'expires': now + 60})


class MockSuppressionManager(SuppressionManager):
    def migrate_suppressions(self):
        return

    def get_suppressions(self, expire, include_disabled=False):
        suppressions = copy.deepcopy(SUPPRESSIONS)
        for s in suppressions:
            s.update(SUPPRESSION_COMMON)
        return ([Suppression(x) for x in suppressions], None)


class TestBase(unittest.TestCase):
    def setUp(self):
        self.suppression_manager = MockSuppressionManager(
            cache_ttl=60, schema_class=Suppression)

    def test_is_suppressed(self):
        self.assertFalse(self.suppression_manager.is_suppressed('woot'))
        self.assertTrue(self.suppression_manager.is_suppressed('test_foo'))
        self.assertTrue(self.suppression_manager.is_suppressed('test_barn'))
