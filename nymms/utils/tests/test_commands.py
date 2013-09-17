import unittest

from nymms.utils import commands


class TestCommands(unittest.TestCase):
    def test_execute_failure(self):
        with self.assertRaises(commands.CommandFailure):
            # Non-existant command
            out = commands.execute('xxxps auwwwx', 10)

    def test_execute_timeout(self):
        with self.assertRaises(commands.CommandTimeout):
            out = commands.execute('sleep 2', 1)

    def test_execute_success(self):
        out = commands.execute('echo test', 10)
        self.assertEqual(out, 'test\n')
