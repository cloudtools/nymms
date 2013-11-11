import unittest
from weakref import WeakValueDictionary

from nymms import resources
from nymms.exceptions import MissingCommandContext


class TestNanoResources(unittest.TestCase):
    def test_reserved_attributes(self):
        with self.assertRaises(TypeError):
            resources.Command(name='test', command_string='test',
                              address='10.0.0.1')

    def test_resource_context(self):
        c = resources.Command(name='test', command_string='test')
        context = c._context()
        self.assertEqual(context.keys()[0], 'command')
        self.assertEqual(context['command']['name'], c.name)

    def test_extra_attributes(self):
        extra_attribute_name = 'extra'
        extra2_value = 'extra2'
        c1 = resources.Command(name='test1', command_string='test1')
        c2 = resources.Command(name='test2', command_string='test2',
                               extra=extra2_value)
        with self.assertRaises(KeyError):
            c1.extra_attributes[extra_attribute_name]
        self.assertEquals(c2.extra_attributes[extra_attribute_name],
                          extra2_value)


class TestNode(unittest.TestCase):
    def test_adding_monitoring_groups(self):
        mg1 = resources.MonitoringGroup('mg1')
        self.assertEqual(mg1.nodes, WeakValueDictionary())
        mg2 = resources.MonitoringGroup('mg2')
        self.assertEqual(mg2.nodes, WeakValueDictionary())
        node = resources.Node(name='node1', address='127.0.0.1',
                              monitoring_groups=[mg1, mg2])
        self.assertIn(node, mg1.nodes.values())
        self.assertIn(node, mg2.nodes.values())


class TestCommand(unittest.TestCase):
    def test_format_command(self):
        command = "/bin/echo {{public}} {{__private.password}}"
        context = {'public': 'public'}
        private_context = {'password': 'mypassword'}
        c = resources.Command('echo', command)
        with self.assertRaises(MissingCommandContext):
            c.format_command(context)
        c_out = c.format_command(context, private_context)
        self.assertEquals(c_out,
                          "/bin/echo public mypassword")
