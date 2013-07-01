import logging
import os
import imp
import copy
from weakref import WeakValueDictionary

from nymms import registry
from nymms.utils import commands

logger = logging.getLogger(__name__)

from nymms.config import settings

RESERVED_ATTRIBUTES = ['name', 'address', 'node_monitor', 'monitoring_groups',
        'command_string']


def load_resources(resource_path):
    logger.info("Loading local resources from %s." % (resource_path))
    resource_path = os.path.expanduser(resource_path)
    path, module = os.path.split(resource_path)

    if module.endswith('.py'):
        module = module[:-3]

    try:
        module_info = imp.find_module(module, [path])
        local_resources = imp.load_module('local_resources', *module_info)
    finally:
        if module_info[0]:
            module_info[0].close()
    return local_resources


class RegistryMetaClass(type):
    """ Creates a registry of all objects of a classes type.

    This allows us to get a list of all objects of a given class type quickly
    and easily.  IE:

    >>> from nymms import resources
    >>> webservers = resources.MonitoringGroup('webservers')
    >>> www1 = resources.Node('www1', monitoring_groups=[webservers])
    >>> resources.Node.registry.items()
    [('www1', <nymms.resources.Node object at 0x10b6aa8d0>)]
    """
    def __new__(cls, name, bases, dct):
        new_class = super(RegistryMetaClass, cls).__new__(cls, name, bases,
                dct)
        new_class.registry = registry.Registry(new_class)
        return new_class


class NanoResource(object):
    __metaclass__ = RegistryMetaClass

    context_attributes = ['name',]

    def __init__(self, name, **kwargs):
        self.name = name
        # Ensure noone tries to set a reserved attribute as an extra
        disallowed_attributes = list(
                set(RESERVED_ATTRIBUTES) & set(kwargs.keys()))
        if disallowed_attributes:
            raise TypeError("The following are reserved attributes and cannot "
                    "be used on this resource: %s" % (', '.join(
                        disallowed_attributes)))
        self.extra_attributes = kwargs
        self._context_cache = None

        self.register()

    def register(self):
        logger.debug("Registering %s resource '%s' with the '%s' registry." % (
            self.__class__.__name__, self.name, self.__class__.__name__))
        self.registry[self.name] = self

    def _context(self, force=False):
        if self._context_cache and not force:
            logger.debug("Returning context cache for %s resource." % (
                    self.name))
            return self._context_cache
        logger.debug("Generating context cache for %s resource." % (self.name))
        context_key = self.__class__.__name__.lower()
        context = {}
        for attr in self.context_attributes:
            context[attr] = getattr(self, attr)
        for k, v in self.extra_attributes.items():
            context[k] = v
        self._context_cache = {context_key: context}
        return self._context_cache


class MonitoringGroup(NanoResource):
    def __init__(self, name, monitors=None, nodes=None, **kwargs):
        self.nodes = WeakValueDictionary()
        self.monitors = WeakValueDictionary()

        if monitors:
            for monitor in monitors:
                self.add_monitor(monitor)
        if nodes:
            for node in nodes:
                self.add_node(node)

        super(MonitoringGroup, self).__init__(name, **kwargs)

    def add_node(self, node):
        logger.debug("Adding node '%s' to monitoring group '%s'." % (node.name,
            self.name))
        self.nodes[node.name] = node
        node.monitoring_groups[self.name] = self

    def add_monitor(self, monitor):
        logger.debug("Adding monitor '%s' to monitoring group '%s'." % (
            monitor.name, self.name))
        self.monitors[monitor.name] = monitor
        monitor.monitoring_groups[self.name] = self


class Node(NanoResource):
    context_attributes = ['name', 'address', 'node_monitor']

    def __init__(self, name, address=None, node_monitor=None,
            monitoring_groups=None, **kwargs):
        self.name = name
        self.address = address or name
        self.node_monitor = node_monitor
        self.monitoring_groups = WeakValueDictionary()
        self._tasks = []
        if monitoring_groups:
            for group in monitoring_groups:
                if isinstance(group, MonitoringGroup):
                    g = group
                else:
                    g = MonitoringGroup.registry[group]
                g.add_node(self)

        super(Node, self).__init__(name, **kwargs)

    def monitors(self):
        monitor_dict = {}
        for group_name, group in self.monitoring_groups.iteritems():
            monitor_dict[group_name] = {}
            for monitor_name, monitor in group.monitors.iteritems():
                monitor_dict[group_name][monitor_name] = monitor
        return monitor_dict

    def build_context(self, monitoring_group, monitor):
        context = {}
        for obj in (monitoring_group, self, monitor):
            c = obj._context()
            context.update(c)
            for k, v in c.values()[0].iteritems():
                if not k == 'name':
                    context[k] = v
        return context

    @property
    def tasks(self):
        if self._tasks:
            return self._tasks
        for group_name, group in self.monitoring_groups.iteritems():
            for monitor_name, monitor in group.monitors.iteritems():
                self._tasks.append(self.build_context(group, monitor))
        return self._tasks


class Monitor(NanoResource):
    context_attributes = ['name']

    def __init__(self, name, command, monitoring_groups=None, **kwargs):
        self.name = name
        self.command = command
        self.monitoring_groups = WeakValueDictionary()
        if monitoring_groups:
            for group in monitoring_groups:
                group.add_monitor(self)

        super(Monitor, self).__init__(name, **kwargs)

    def execute(self, context, timeout=settings.monitor_timeout):
        return self.command.execute(context, timeout)

    def format_command(self, context):
        return self.command.format_command(context)


class Command(NanoResource):
    context_attributes = ['name', 'command_type', 'command_string']

    def __init__(self, name, command_string, command_type='nagios', **kwargs):
        self.command_type = command_type
        self.command_string = command_string
        super(Command, self).__init__(name, **kwargs)

    def format_command(self, context):
        my_context = self._context()
        local_context = copy.deepcopy(context)
        local_context.update(my_context)
        for k, v in my_context.values()[0].iteritems():
            if not k == 'name' and not k in local_context:
                local_context[k] = v
        return self.command_string.format(**local_context)

    def execute(self, context, timeout=settings.monitor_timeout):
