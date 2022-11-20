import logging
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self, logger):
        self.logger = logger
        self.config = None

    def load_yaml(self, filename):
        self.logger.log_message(
            logging.DEBUG, 'Using YAML loader {}'.format(SafeLoader))
        self.logger.log_message(
            logging.INFO, "Using config file '{}'".format(filename))
        with open(filename, mode="rt", encoding="utf-8") as file:
            self.config = yaml.load(file, SafeLoader)
        if self.config is None:
            self.logger.log_message(
                logging.ERROR, 'Unable to read config file')

    def list_backups(self):
        return self.config['backups'].keys()

    def get_backup_config(self, backup):
        return self.config['backups'][backup]


def load_yaml(filename, logger):
    config = Configuration(logger)
    config.load_yaml(filename)
    return config
