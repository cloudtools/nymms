import unittest

from nymms import utils
from nymms.exceptions import InvalidTimeFormat


class TestBase(unittest.TestCase):
    def test_load_class_from_string(self):
        from logging import Logger
        cls = utils.load_object_from_string('logging.Logger')
        self.assertIs(cls, Logger)

    def test_parse_time(self):
        base_time = 1415311935
        self.assertEqual(utils.parse_time('+60s', base_time), base_time + 60)
        self.assertEqual(utils.parse_time('+10m', base_time),
                         base_time + (60 * 10))
        self.assertEqual(utils.parse_time('+10h', base_time),
                         base_time + (60 * 60 * 10))
        self.assertEqual(utils.parse_time('-10d', base_time),
                         base_time - (10 * 60 * 60 * 24))
        with self.assertRaises(InvalidTimeFormat):
            utils.parse_time('+2000xxx')
