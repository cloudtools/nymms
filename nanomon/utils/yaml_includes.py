import yaml
import os

class IncludeLoader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(IncludeLoader, self).__init__(stream)

    def include(self, node):
        filename = self.construct_scalar(node)
        if not filename.startswith('/'):
            filename = os.path.join(self._root, filename)

        with open(filename, 'r') as f:
            return yaml.load(f, IncludeLoader)


IncludeLoader.add_constructor('!include', IncludeLoader.include)

def load_config(config_file='config.yaml'):
    with open(config_file) as fd:
        return yaml.load(fd, IncludeLoader)
