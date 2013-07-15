import os
import logging
import copy

logger = logging.getLogger(__name__)

from nymms.config import yaml_config

DEFAULTS = {}

config_path = os.path.expanduser(os.environ.get('NYMMS_CONFIG',
        '/etc/nymms/nymms.yaml'))

settings = copy.deepcopy(DEFAULTS)
settings.update(yaml_config.load_config(config_path))
