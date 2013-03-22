from nanomon import registry

RESERVED_ATTRIBUTES = ['name', 'address', 'host_monitor', 'monitoring_groups',
        'command_string']

class NanoResource(object):
    registry = None
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
        self.registry[self.name] = self

    def generate_context(self, force=False):
        if self._context_cache and not force:
            return self._context_cache
        context_key = self.__class__.__name__.lower()
        context = {}
        for attr in self.context_attributes:
            context[attr] = getattr(self, attr)
        for k, v in self.extra_attributes.items():
            context[k] = v
        self._context_cache = {context_key: context}
        return self._context_cache


class MonitoringGroup(NanoResource):
    registry = registry.monitoring_groups

    def __init__(self, name, **kwargs):
        self.hosts = {}
        self.monitors = {}
        super(MonitoringGroup, self).__init__(name, **kwargs)

    def add_host(self, host):
        self.hosts[host.name] = host
        host.monitoring_groups[self.name] = self

    def add_monitor(self, monitor):
        self.monitors[monitor.name] = monitor
        monitor.monitoring_groups[self.name] = self


class Host(NanoResource):
    registry = registry.hosts
    context_attributes = ['name', 'address', 'host_monitor']

    def __init__(self, name, address=None, host_monitor=None,
            monitoring_groups=set(), **kwargs):
        self.name = name
        self.address = address or name
        self.host_monitor = host_monitor
        self.monitoring_groups = {}
        for group in monitoring_groups:
            group.add_host(self)
        super(Host, self).__init__(name, **kwargs)

    def monitors(self):
        monitor_dict = {}
        for group_name, group in self.monitoring_groups.iteritems():
            monitor_dict[group_name] = {}
            for monitor_name, monitor in group.monitors.iteritems():
                monitor_dict[group_name][monitor_name] = monitor
        return monitor_dict

    def build_context(self, monitoring_group, monitor):
        if monitor._monitor_context:
            return monitor._monitor_context

        context = {}
        for obj in (monitor.command, monitoring_group, self, monitor):
            c = obj.generate_context()
            context.update(c)
            for k, v in c.values()[0].iteritems():
                if not k == 'name':
                    context[k] = v
        monitor._monitor_context = context
        return context



class Monitor(NanoResource):
    registry = registry.monitors
    context_attributes = ['name']

    def __init__(self, name, command, monitoring_groups, **kwargs):
        self._monitor_context = None
        self.name = name
        self.command = command
        self.monitoring_groups = {}
        for group in monitoring_groups:
            group.add_monitor(self)

        super(Monitor, self).__init__(name, **kwargs)


class Command(NanoResource):
    registry = registry.commands
    context_attributes = ['name', 'command_string']

    def __init__(self, name, command_string, **kwargs):
        self.command_string = command_string
        super(Command, self).__init__(name, **kwargs)
