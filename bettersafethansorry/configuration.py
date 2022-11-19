import logging
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self):
        self.configuration = None

    def load_yaml(self, filename):
        logger.debug("Using YAML loader {}".format(SafeLoader))
        logger.info("Reading configuration file '{}'".format(filename))
        with open(filename, mode="rt", encoding="utf-8") as file:
            self.configuration = yaml.load(file, SafeLoader)
    
    def list_backups(self):
        return self.configuration['backups'].keys()


def load_yaml(filename):
    configuration = Configuration()
    configuration.load_yaml(filename)
    return configuration

