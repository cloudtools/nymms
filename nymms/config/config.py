import logging
import copy

logger = logging.getLogger(__name__)

from nymms.config import yaml_config

DEFAULTS = {}

settings = None
version = None


def load_config(path, force=False):
    global settings, version, DEFAULTS
    if settings and not force:
        return
    settings = copy.deepcopy(DEFAULTS)
    version, __config_settings = yaml_config.load_config(path)
    settings.update(__config_settings)
    logger.debug("Config loaded from '%s' with version '%s'." % (path,
                                                                 version))
