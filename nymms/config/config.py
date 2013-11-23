import logging
import copy
import os
import collections

logger = logging.getLogger(__name__)

validator = None
try:
    import validictory
    validator = validictory.validate
except ImportError:
    logger.warning("Unable to import validictory - skipping config "
                   "validation.")

from nymms.config import yaml_config
from nymms.utils import deep_update
from nymms import exceptions


default_conf_dir = '/etc/nymms'

SCHEMA = {
    'type': 'object',
    'properties': {
        'monitor_timeout': {
            'type': 'integer', 'minimum': 0,
        },
        'resources': {
            'type': 'string',
        },
        'region': {
            'type': 'string',
        },
        'state_domain': {
            'type': 'string',
        },
        'tasks_queue': {
            'type': 'string',
        },
        'results_topic': {
            'type': 'string',
        },
        'private_context_file': {
            'type': 'string',
        },
        'task_expiration': {
            'type': 'integer', 'minimum': 0,
        },
        'probe': {
            'type': 'object',
            'properties': {
                'max_retries': {
                    'type': 'integer', 'minimum': 0,
                },
                'queue_wait_time': {
                    'type': 'integer', 'minimum': 0, 'maximum': 20,
                },
                'retry_delay': {
                    'type': 'integer', 'minimum': 0,
                },
            }
        },
        'reactor': {
            'type': 'object',
            'properties': {
                'handler_config_path': {
                    'type': 'string',
                },
                'queue_name': {
                    'type': 'string',
                },
                'queue_wait_time': {
                    'type': 'integer', 'minimum': 0, 'maximum': 20,
                },
                'visibility_timeout': {
                    'type': 'integer', 'minimum': 5,
                },
            },
        },
        'scheduler': {
            'type': 'object',
            'properties': {
                'interval': {
                    'type': 'integer', 'minimum': 30,
                },
                'backend': {
                    'type': 'string',
                },
                'backend_args': {
                    'type': 'object',
                },
            },
        },
    }
}

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
    if validator:
        try:
            validator(settings, SCHEMA)
        except ValueError as e:
            raise exceptions.InvalidConfig(path, e.message)
    logger.debug("Config loaded from '%s' with version '%s'." % (path,
                                                                 version))
