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

    queue_wait_time
        The amount of time the probe will wait for a task to appear in the
        tasks_queue. AWS SQS only allows this to be a maximum of 20 seconds.
        In most cases, the default should be fine.
        *Type:* Integer. *Default:* 20

    retry_delay
        The amount of time in seconds that a probe will delay retries on
        non-OK, non-HARD monitors.  This allows you to quickly retry monitors
        that are supposed to be failing, to verify that there is an actual
        issue.
        *Type:* Integer. *Default:* 30

reactor
    This is a dictionary where reactor specific configuration goes.
    *Type:* Dictionary

    handler_config_path
        The directory where `Reactor Handlers`_ specific configurations are
        found.
        *Type:* String. *Default:* /etc/nymms/handlers

    queue_name
        The name of the SQS queue where reactions will be found.
        *Type:* String. *Default:* reactor_queue

    queue_wait_time
        The amount of time the probe will wait for a result to appear in the
        queue named in reactor.queue_name. AWS SQS only allows this to be a
        maximum of 20 seconds.
        In most cases, the default should be fine.
        *Type:* Integer. *Default:* 20

    visibility_timeout
        The amount of time (in seconds) that a message will disappear from the
        SQS reactor queue (defined in reactor.queue_name above) when it is
        picked up by a reactor. If the reactor doesn't finish it's work and
        delete the message within this amount of time, the message will
        re-appear in the queue. This allows the reactions to survive reactor
        crashes and the like.
        *Type:* Integer. *Default:* 30

scheduler
    This is a dictionary where reactor specific configuration goes.
    *Type:* Dictionary

    interval
        How often, in seconds, the scheduler will schedule tasks.
        *Type:* Integer. *Default:* 300

    backend
        The dot-separated class path to use for the backend. The backend
        is what is used to find nodes that need to be monitored.
        *Type:* String.
        *Default:* nymms.scheduler.backends.yaml_backend.YamlBackend

    backend_args
        Any configuration args that the scheduler.backend above needs.
        *Type:* Dictionary

        path
            This is used by the YamlBackend, which is the default. This
            gives the name of the yaml file with node definitions that
            the YamlBackend uses.
            *Type:* String. *Default:* /etc/nymms/nodes.yaml

    lock_backend
        The backend used for locking multiple schedulers. Currently only
        SDB is available.
        *Type:* String. *Default:* SDB

    lock_args
        Any configuration args that the scheduler.lock_backend needs.
        *Type:* Dictionary.

        duration
            How long, in seconds, the scheduler will keep the lock for.
            *Type:* Integer. *Default:* 360

        domain_name
            The SDB domain name where locks are stored.
            *Type:* String. *Default:* nymms_locks

        lock_name
            The name of the lock.
            *Type:* String. *Default:* scheduler_lock


suppress
    These are the config settings used by the suppression system.
    *Type:* Dictionary.

        domain
            The SDB domain where suppressions will be stored.
            *Type:* String. *Default:* nymms_suppress

        cache_timeout
            The amount of time, in seconds, to keep suppressions cached.
            *Type:* Integer. *Default:* 60


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
