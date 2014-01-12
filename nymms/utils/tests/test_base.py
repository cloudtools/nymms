import unittest

from nymms import utils


class DummyClass(object):
    pass


class TestBase(unittest.TestCase):
    def test_load_class_from_string(self):
        from logging import Logger
        cls = utils.load_object_from_string('logging.Logger')
        self.assertIs(cls, Logger)
