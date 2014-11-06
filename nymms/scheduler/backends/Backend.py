import logging

from nymms.resources import load_resource, Node
from nymms.registry import DuplicateEntryError

logger = logging.getLogger(__name__)


class Backend(object):
    def _load_nodes(self):
        """ Should return a dictionary of Node information in this form:
        {'<node_name>': {<node creation kwargs>}, ...}

        Meant to be overridden by subclasses.
        """
        raise NotImplementedError

    def load_nodes(self, reset=False):
        nodes = self._load_nodes()
        try:
            load_resource(nodes, Node, reset=reset)
        except DuplicateEntryError:
            # TODO: Need to figure out the story for reloading nodes, etc.
            logger.debug("Nodes already loaded and reset is False, skipping.")
