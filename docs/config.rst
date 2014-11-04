=============
Configuration
=============

The default configuration language for NYMMS is written in `YAML`_. For the
most part it follows the YAML_ standard. It has one main addition, the
!include macro.

!include can be used to include another file in a given file. This is useful
when you have a main config file (say nodes.yaml_) but want to allow external
programs to provide more config (say in /etc/nymms/nodes/\*.yaml).

In that specific example you'd put the following in the yaml file where you
want the files included::

    !include /etc/nymms/nodes/*.yaml

config.yaml
===========

The config.yaml file is the main configuration for all of the daemons and
scripts in NYMMS.

You can see an example by expanding the code block below.

.. hidden-code-block:: yaml
    :starthidden: True
    :label: Example config.yaml

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

The resources.yaml file is where you define your commands, monitors and
monitoring groups.

commands
    Commands are where you define the commands that will be used for
    monitoring services.  The main config for each command is the
    *command_string*, which is a templatized string that defines the command
    line to a command line executable.

monitors
    Monitors are specific instances of commands, allowing you to fill in
    templated variables in the command used.  This allows your commands to
    be fairly generic and easily re-usable.

monitoring groups
    Monitoring groups are used to tie monitors to individual nodes.  It also
    lets you add some monitoring group specific variables that can be used in
    commands templates and other places.

.. hidden-code-block:: yaml
    :starthidden: True
    :label: Example resources.yaml

    commands:
      check_https:
        command_string: /usr/lib/nagios/plugins/check_http -H {{address}} -S -u {{url}} -m {{minimum_size}} -w {{warn_timeout}} -c {{crit_timeout}}
        warn_timeout: 1
        crit_timeout: 10
      check_http:
        command_string: /usr/lib/nagios/plugins/check_http -H {{address}} -u {{url}} -w {{warn_timeout}} -c {{crit_timeout}}
        warn_timeout: 1
        crit_timeout: 10
      check_https_cert:
        command_string: /usr/lib/nagios/plugins/check_http -H {{address}} -S -u {{url}} -C {{cert_days}}
      check_file:
        command_string: /usr/bin/test -f {{file_name}}

    monitoring_groups:
      all:
      local:
      google:

    monitors:
      google_http:
        command: check_http
        url: /
        monitoring_groups:
          - google
      file_tmp_woot:
        command: check_file
        file_name: /tmp/woot
        monitoring_groups:
          - local

Config Options
--------------

commands
    A dictionary of commands, the key of each is a unique name for the command,
    and the value is another dictionary with the commands configuration.
    Other than the *command_string* config option, you can specify any others
    you like - they will be accessible in the template of the *command_string*
    itself.
    *Type:* Dictionary.

    command_string
        A command line string using Jinja's variable syntax. (ie:
        {{variable}}).
        *Type:* String.

    *other configs*
        You can specify as many other key/value entries as you like. They will
        be useable as variables in the *command_string* itself. Often times the
        values set here will be used as defaults for the command, provided
        the variable isn't set anywhere else (such as on the monitor, or the
        node).

monitors
    A dictionary of monitors, each of which calls a command defined above. The
    key of each entry is the name of the monitor, the value is another
    dictionary which contains configuration values for that monitor.
    *Type:* Dictionary

    command
        The name of a command defined in the resources file. This is the
        command that will be called for this monitor.
        *Type:* String.

    monitoring_groups
        A list of monitoring groups that this monitor is a part of. This is
        how you tie monitors to nodes - every monitor that is attached to
        a monitoring_group will be ran against every node that is attached
        to that monitoring_group.

    *other configs*
        You can specify as many other key/value entries as you like for each
        monitor. They will be useable as variables in the template strings used
        in the command for this monitor.


monitoring_groups
    A dictionary of monitoring groups which tie together monitors and nodes.
    The keys of the dictionary are the monitoring_groups names, while the
    values are any extra config you want to put into the command context.
    Often times the values will be blank (see the example).


private.yaml
============

The private.yaml file is used to give context variables that can be used in
various monitors, but which are not included when the tasks and results are
sent over the wire. Largely these are used for things like passwords that
are needed by monitors.

The variables that are provided by private.yaml need to be prepended by 
*__private.* when referring to them in templates. For example, if you have
a private variable called *db_password* you would refer to it as
*__private.db_password* in templates.

The contents of the private.yaml are simple key/value pairs.

.. hidden-code-block:: yaml
    :starthidden: True
    :label: Example private.yaml

    example_password: example
    db_password: db_password

nodes.yaml
==========

The nodes.yaml file is the file used by default by the YamlBackend, which is
used by the scheduler to figure out what nodes (instances, hosts, etc) need
to be monitored. It's a dictionary of node entries - each entry's key is
the name of the node. The value of each entry is a dictionary with the
following options:

.. hidden-code-block:: yaml
    :starthidden: True
    :label: Example nodes.yaml

    !include /etc/nymms/nodes/\*.yaml

    local:
      monitoring_groups:
        - local
    www.google.com:
      monitoring_groups:
        - google

address
    The network address of the node. This can be an ip address, or a hostname.
    If no address is provided, then it is assumed that the name of the node
    entry is the address.
    *Type:* String. *Default:* The node entry name.

monitoring_groups
    A list of monitoring groups (as defined in resources.yaml) that this node
    is part of. Every monitor that is attached to a monitoring group will be
    applied to every node in the monitoring group.
    *Type:* List.

realm
    The realm this node is a part of.  See the realms_ documentation.

Reactor Handlers
================

.. _YAML: http://www.yaml.org/
.. _realms: realms.html
