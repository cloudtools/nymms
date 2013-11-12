import logging

logger = logging.getLogger(__name__)

import copy
from weakref import WeakValueDictionary

from nymms import registry
from nymms.utils import commands
from nymms.config import yaml_config
from nymms.exceptions import MissingCommandContext

from jinja2 import Template
from jinja2.runtime import StrictUndefined
from jinja2.exceptions import UndefinedError


RESERVED_ATTRIBUTES = ['name', 'address', 'node_monitor', 'monitoring_groups',
                       'command_string']


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

    context_attributes = ['name']

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
    context_attributes = ['name', 'realm']

    def __init__(self, name, realm=None, monitors=None, nodes=None, **kwargs):
        self.nodes = WeakValueDictionary()
        self.monitors = WeakValueDictionary()
        self.realm = realm

        super(MonitoringGroup, self).__init__(name, **kwargs)

        if monitors:
            for monitor in monitors:
                self.add_monitor(monitor)
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node):
        if not isinstance(node, Node):
            try:
                node = Node.registry[node]
            except KeyError:
                logger.error("Unable to find Node '%s' in registry." % (
                    node))
        logger.debug("Adding node '%s' to monitoring group '%s'." % (node.name,
                     self.name))
        self.nodes[node.name] = node
        node.monitoring_groups[self.name] = self

    def add_monitor(self, monitor):
        if not isinstance(monitor, Monitor):
            try:
                monitor = Monitor.registry[monitor]
            except KeyError:
                logger.error("Unable to find Monitor '%s' in registry." % (
                    monitor))
        logger.debug("Adding monitor '%s' to monitoring group '%s'." % (
            monitor.name, self.name))
        self.monitors[monitor.name] = monitor
        monitor.monitoring_groups[self.name] = self


class Node(NanoResource):
    context_attributes = ['name', 'realm', 'address', 'node_monitor']

    def __init__(self, name, realm=None, address=None, node_monitor=None,
                 monitoring_groups=None, **kwargs):
        self.name = name
        self.realm = realm
        self.address = address or name
        self.node_monitor = node_monitor
        self.monitoring_groups = WeakValueDictionary()
        self._tasks = []
        if monitoring_groups:
            for group in monitoring_groups:
                if not isinstance(group, MonitoringGroup):
                    try:
                        group = MonitoringGroup.registry[group]
                    except KeyError:
                        logger.error("Unable to find MonitoringGroup '%s' "
                                     "in registry, skipping." % (group))
                group.add_node(self)

        super(Node, self).__init__(name, **kwargs)

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
    def monitors(self):
        if self._tasks:
            return self._tasks
        for group_name, group in self.monitoring_groups.iteritems():
            for monitor_name, monitor in group.monitors.iteritems():
                self._tasks.append(self.build_context(group, monitor))
        return self._tasks


class Monitor(NanoResource):
    context_attributes = ['name', 'realm']

    def __init__(self, name, command, realm=None, monitoring_groups=None,
                 **kwargs):
        self.name = name
        self.realm = realm
        if not isinstance(command, Command):
            try:
                command = Command.registry[command]
            except KeyError:
                logger.error("Unable to find Command '%s' in registry." % (
                    command))
                raise

        self.command = command
        self.monitoring_groups = WeakValueDictionary()
        if monitoring_groups:
            for group in monitoring_groups:
                if not isinstance(group, MonitoringGroup):
                    try:
                        group = MonitoringGroup.registry[group]
                    except KeyError:
                        logger.error("Unable to find MonitoringGroup '%s' in "
                                     "registry." % (group))
                        raise
                group.add_monitor(self)

        super(Monitor, self).__init__(name, **kwargs)

    def execute(self, context, timeout, private_context=None):
        return self.command.execute(context, timeout, private_context)

    def format_command(self, context, private_context=None):
        return self.command.format_command(context, private_context)


class Command(NanoResource):
    context_attributes = ['name', 'command_type', 'command_string']

    def __init__(self, name, command_string, command_type='nagios', **kwargs):
        self.command_type = command_type
        self.command_string = command_string
        super(Command, self).__init__(name, **kwargs)

    def format_command(self, context, private_context=None):
        my_context = self._context()
        local_context = copy.deepcopy(context)
        local_context.update(my_context)
        local_context['__private'] = {}
        if private_context:
            local_context['__private'].update(private_context)
        for k, v in my_context.values()[0].iteritems():
            if not k == 'name' and not k in local_context:
                local_context[k] = v
        t = Template(self.command_string)
        t.environment.undefined = StrictUndefined
        try:
            out = t.render(local_context)
        except UndefinedError as e:
            raise MissingCommandContext(e.message)
        return t.render(local_context)

    def execute(self, context, timeout, private_context=None):
        cmd = self.format_command(context, private_context)
        return commands.execute(cmd, timeout)


def load_resource(resources, resource_class, reset=False):
    """ Given a dictionary of a given resource_type, instantiate them.

    The resources are loaded into the given resource registry.
    """
    if reset:
        logger.debug("Clearing old %s entries from registry." % (
            resource_class.__name__))
        resource_class.registry.clear()

    for name, kwargs in resources.items():
        if not kwargs:
            kwargs = {}
        resource_class(name, **kwargs)


def load_resources(resource_file, reset=False):
    """ Loads resources in yaml formatted resource_file in the proper order.

    Returns a sha512 hash of the resources.  The resources themselves are
    stored in their individual registries.
    """
    LOAD_ORDER = [('commands', Command),
                  ('monitoring_groups', MonitoringGroup),
                  ('monitors', Monitor)]

    logger.info("Loading local resources from %s." % (resource_file))
    version, resources = yaml_config.load_config(resource_file)

    for resource_type, resource_class in LOAD_ORDER:
        items = resources[resource_type]
        load_resource(items, resource_class, reset=reset)
    return version


def load_nodes(node_file, reset=False):
    """ Loads nodes from a yaml formatted file.

    Nodes are stored in the Node registry.
    """
    logger.info("Loading nodes from %s." % (node_file))
    version, nodes = yaml_config.load_config(node_file)

    items = nodes['nodes']
    load_resource(items, Node, reset=reset)
    return version
