import unittest

from nanomon.utils import yaml_includes


class TestIncludeLoader(unittest.TestCase):
    def test_relative_include(self):
        relative_config = yaml_includes.load_config(
                'utils/tests/test_include.yaml')
        self.assertEqual(relative_config['relative_include']['foo'], 'bar')
