import os
import logging
import copy

logger = logging.getLogger(__name__)

from nymms.config import yaml_config

DEFAULTS = {}

config_path = os.path.expanduser(os.environ.get('NYMMS_CONFIG',
        '/etc/nymms/nymms.yaml'))

settings = copy.deepcopy(DEFAULTS)
version = None

def reload_config():
    """ Used to manually reload the config.
    """
    global settings, version, DEFAULTS
    settings = copy.deepcopy(DEFAULTS)
    version, __config_settings = yaml_config.load_config(config_path)
    settings.update(__config_settings)
    logger.debug("Config loaded from '%s' with version '%s'." % (config_path,
        version))

# Only ran once, no matter how many times the module is imported.
reload_config()
