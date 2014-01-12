import unittest

from nymms.reactor.Reactor import Reactor
from nymms.reactor.handlers.Handler import Handler


enabled_config = {'handler_class': 'nymms.reactor.handlers.Handler.Handler',
                  'enabled': True}
disabled_config = {'handler_class': 'nymms.reactor.handlers.Handler.Handler',
                   'enabled': False}


class TestReactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reactor = Reactor()

    def test_load_enabled_handler(self):
        handler = self.reactor._load_handler('dummy_handler', enabled_config)
        self.assertIsInstance(handler, Handler)

    def test_load_disabled_handler(self):
        handler = self.reactor._load_handler('dummy_handler', disabled_config)
        self.assertIs(handler, None)
