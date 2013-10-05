import logging

from nymms.scheduler.backends.Backend import Backend
from nymms.config import yaml_config

logger = logging.getLogger(__name__)


class YamlBackend(Backend):
    def __init__(self, path):
        self.path = path

    def load_nodes(self):
        version, nodes = yaml_config.load_config(self.path)
        logger.debug("Loaded node config (%s) from %s.", version, self.path)
        return nodes
