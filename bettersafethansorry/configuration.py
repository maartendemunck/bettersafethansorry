import logging
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self):
        self.config = None

    def load_yaml(self, filename):
        logger.debug("Using YAML loader {}".format(SafeLoader))
        logger.info("Reading config file '{}'".format(filename))
        with open(filename, mode="rt", encoding="utf-8") as file:
            self.config = yaml.load(file, SafeLoader)

    def list_backups(self):
        return self.config['backups'].keys()

    def get_backup_config(self, backup):
        return self.config['backups'][backup]['actions']


def load_yaml(filename):
    config = Configuration()
    config.load_yaml(filename)
    return config
