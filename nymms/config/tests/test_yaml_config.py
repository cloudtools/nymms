import unittest
import os

from nymms.config import yaml_config


class TestIncludeLoader(unittest.TestCase):
    def setUp(self):
        self.root = os.path.split(__file__)[0]

    def test_relative_include(self):
        full_path = os.path.join(self.root, 'config.yaml')
        version, relative_config = yaml_config.load_config(full_path)
        self.assertEqual(relative_config['foo'], 'bar')
        self.assertEqual(relative_config['file1'], 1)

    def test_missing_config(self):
        with self.assertRaises(IOError):
            yaml_config.load_config('nonexistant.yaml')
