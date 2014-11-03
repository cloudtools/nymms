=============
Configuration
=============

config.yaml
===========

The config.yaml file is the main configuration for all of the daemons and
scripts in NYMMS.

monitor_timeout
    This represents the default amount of time, in seconds, each monitor is
    given before it times out.
    *Type:* Integer. *Default:* 30

resources
    This points to the filesystem location of the resources config (see
    resources.yaml_).
    *Type:* String, file location. *Default:* /etc/nymms/resources.yaml

region
    The AWS region used by the various daemons.
    *Type:* String, AWS Region. *Default:* us-east-1

state_domain
    The SDB domain used for storing state.
    *Type:* String. *Default:* nymms_state

tasks_queue
    The name of the SQS queue used for distributing tasks.
    *Type:* String. *Default:* nymms_tasks

results_topic
    The name of the SNS topic where results are sent.
    *Type:* String. *Default:* nymms_results

private_context_file
    The location of the private context file (see private.yaml_).
    *Type:* String, file location. *Default:* /etc/nymms/private.yaml

task_expiration
    If a task is found by a probe, and it is older than this time in seconds,
    then the probe will throw it away.
    *Type:* Integer. *Default:* 600

probe
    This is a dictionary where probe specific configuration goes.
    *Type:* Dictionary.

    max_retries
        The maximum amount of times the probe will retry a monitor that is in
        a non-OK state.
        *Type:* Integer. *Default:* 2

    queue_wait_time:
        The amount of time the probe will wait for a task to appear in the
        tasks_queue. AWS SQS only allows this to be a maximum of 20 seconds.
        In most cases, the default should be fine.
        *Type:* Integer. *Default:* 20
        

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
