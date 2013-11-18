import logging
import copy
import os
import collections

logger = logging.getLogger(__name__)

from nymms.config import yaml_config


def deep_update(orig, upd):
    """ Does a 'deep' update of dictionary 'orig' with dictionary 'upd'."""
    for k, v in upd.iteritems():
        if isinstance(v, collections.Mapping):
            r = deep_update(orig.get(k, {}), v)
            orig[k] = r
        else:
            orig[k] = upd[k]
    return orig 

default_conf_dir = '/etc/nymms'

DEFAULTS = {
    'monitor_timeout': 15,
    'resources': os.path.join(default_conf_dir, 'resources.yaml'),
    'region': 'us-east-1',
    'state_domain': 'nymms_state',
    'tasks_queue': 'nymms_tasks',
    'results_topic': 'nymms_results',
    'private_context_file': os.path.join(default_conf_dir, 'private.yaml'),
    'task_expiration': 600,

    'probe': {
        'max_retries': 2,
        'queue_wait_time': 20,
        'retry_delay': 30,
        'blah': 22,
    },

    'reactor': {
        'handler_config_path': os.path.join(default_conf_dir, 'handlers'),
        'queue_name': 'reactor_queue',
        'queue_wait_time': 20,
        'visibility_timeout': 30,
    },

    'scheduler': {
        'interval': 300,
        'backend': 'nymms.scheduler.backends.yaml_backend.YamlBackend',
        'backend_args': {
            'path': os.path.join(default_conf_dir, 'nodes.yaml'),
        }
    },
}

settings = None
version = None


def load_config(path, force=False):
    global settings, version, DEFAULTS
    if settings and not force:
        return
    settings = copy.deepcopy(DEFAULTS)
    version, _config_settings = yaml_config.load_config(path)
    if _config_settings:
        deep_update(settings, _config_settings)
    logger.debug("Config loaded from '%s' with version '%s'." % (path,
                                                                 version))
