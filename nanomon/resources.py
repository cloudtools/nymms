import logging
from weakref import WeakValueDictionary

from nanomon import registry

logger = logging.getLogger(__name__)

RESERVED_ATTRIBUTES = ['name', 'address', 'node_monitor', 'monitoring_groups',
        'command_string']

class RegistryMetaClass(type):
    """ Creates a registry of all objects of a classes type.

    This allows us to get a list of all objects of a given class type quickly
    and easily.  IE:

    >>> from nanomon import resources
    >>> webservers = resources.MonitoringGroup('webservers')
    >>> www1 = resources.Node('www1', monitoring_groups=[webservers])
    >>> resources.Node.registry.items()
    [('www1', <nanomon.resources.Node object at 0x10b6aa8d0>)]
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
    def __init__(self, name, **kwargs):
        self.nodes = WeakValueDictionary()
        self.monitors = WeakValueDictionary()
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
                group.add_node(self)
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
        for obj in (monitor.command, monitoring_group, self, monitor):
            c = obj._context()
            context.update(c)
            for k, v in c.values()[0].iteritems():
                if not k == 'name':
                    context[k] = v
        return context

    def execute_monitors(self):
        results = []
        for group_name, group in self.monitoring_groups.iteritems():
            for monitor_name, monitor in group.monitors.iteritems():
                results.append(monitor.execute(
                        self.build_context(group, monitor)))
        return results

    def generate_command(self, monitoring_group, monitor):
        context = self.build_context(monitoring_group, monitor)
        return monitor.command.command_string.format(**context)

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

    def __init__(self, name, command, monitoring_groups, **kwargs):
        self.name = name
        self.command = command
        self.monitoring_groups = WeakValueDictionary()
        for group in monitoring_groups:
            group.add_monitor(self)

        super(Monitor, self).__init__(name, **kwargs)

    def execute(self, context):
        return self.command.execute(context)


class Command(NanoResource):
    context_attributes = ['name', 'command_string']

    def __init__(self, name, command_string, **kwargs):
        self.command_string = command_string
        super(Command, self).__init__(name, **kwargs)

    def execute(self, context):
        return self.command_string.format(**context)
