import unittest

from nymms import registry
from nymms.resources import Command, MonitoringGroup
from weakref import WeakValueDictionary


class TestRegistry(unittest.TestCase):
    def tearDown(self):
        # Ensure we have a fresh registry after every test
        Command.registry.clear()

    def test_empty_registry(self):
        self.assertEqual(Command.registry, WeakValueDictionary())

    def test_register_object(self):
        # First test it's empty
        self.assertEqual(Command.registry, WeakValueDictionary())
        # Add a command
        command = Command('test_command', '/bin/true')
        # verify that there is only a single command in the registry
        self.assertEqual(len(Command.registry), 1)
        # Verify that the registered command is the same as command
        self.assertIs(Command.registry[command.name], command)

    def test_duplicate_register(self):
        # add a command
        Command('test_command', '/bin/true')
        with self.assertRaises(registry.DuplicateEntryError):
            Command('test_command', '/bin/true')

    def test_invalid_resource_register(self):
        with self.assertRaises(TypeError):
            Command.registry['test'] = MonitoringGroup('test_group')
