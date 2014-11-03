=============
Configuration
=============

config.yaml
===========

The config.yaml file is the main configuration for all of the daemons and
scripts in NYMMS.

*monitor_timeout*
    This represents the default amount of time, in seconds, each monitor is
    given before it times out.
    *Type:* Integer, *Default:* 30

*resources*
    This points to the filesystem location of the resources config (see
    resources.yaml_).
    *Type:* String, file location, *Default:* /etc/nymms/resources.yaml

resources.yaml
==============

nodes.yaml
==========

private.yaml
============

Reactor Handlers
================

More coming soon... here's an example of config.yaml::

    # can be defined on a task by task basis
    monitor_timeout: 15
    resources: /etc/nymms/resources.yaml
    region: us-east-1
    results_topic: nymms_results
    tasks_queue: nymms_tasks
    state_domain: nymms_state

    probe:
      queue_wait_time: 20
    # can be defined on a task by task basis
      max_retries: 3
    # can be defined on a task by task basis
      retry_delay: 10

    scheduler:
      interval: 60
      backend: nymms.scheduler.backends.yaml_backend.YamlBackend
      backend_args:
        path: /etc/nymms/nodes.yaml

    reactor:
      queue_wait_time: 20
      visibility_timeout: 30
      queue_name: reactor_queue
      handler_config_path: /etc/nymms/handlers
