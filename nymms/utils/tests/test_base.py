import unittest

from nymms import utils


class TestBase(unittest.TestCase):
    def test_load_class_from_string(self):
        from logging import Logger
        x = utils.load_object_from_string('logging.Logger')
        self.assertEqual(x, Logger)
