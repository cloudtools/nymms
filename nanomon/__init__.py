from nanomon import registry

class NanoResource(object):
    registry = None

    def __init__(self, name, **kwargs):
        self.name = name
        self.extra_attributes = kwargs

        self.register()

    def register(self):
        self.registry[self.name] = self


class MonitoringGroup(NanoResource):
    registry = registry.monitoring_groups

    def __init__(self, name, **kwargs):
        self.hosts = set()
        self.monitors = set()
        super(MonitoringGroup, self).__init__(name, **kwargs)

    def add_host(self, host):
        self.hosts.add(host)
        host.monitoring_groups.add(self)

    def add_monitor(self, monitor):
        self.monitors.add(monitor)
        monitor.monitoring_groups.add(self)


class Host(NanoResource):
    registry = registry.hosts

    def __init__(self, name, address=None, host_monitor=None,
            monitoring_groups=set(), **kwargs):
        self.address = address or name
        self.host_monitor = host_monitor
        self.monitoring_groups = set()
        for group in monitoring_groups:
            group.add_host(self)
        super(Host, self).__init__(name, **kwargs)

    def monitors(self):
        monitor_dict = {}
        for group in self.monitoring_groups:
            for monitor in group.monitors:
                monitor_dict[monitor.name] = monitor
        return monitor_dict


class Monitor(NanoResource):
    registry = registry.monitors

    def __init__(self, name, command, monitoring_groups, **kwargs):
        self.command = command
        self.monitoring_groups = set()
        for group in monitoring_groups:
            group.add_monitor(self)

        super(Monitor, self).__init__(name, **kwargs)


class Command(NanoResource):
    registry = registry.commands

    def __init__(self, name, command_string, **kwargs):
        self.command_string = command_string
        super(Command, self).__init__(name, **kwargs)
