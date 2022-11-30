import deepmerge
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


class Configuration:

    def __init__(self, logger):
        self.logger = logger
        self.config = None

    def load_yaml(self, filename):
        self.logger.log_debug('Using YAML loader {}'.format(SafeLoader))
        self.logger.log_info("Using config file '{}'".format(filename))
        with open(filename, mode="rt", encoding="utf-8") as file:
            self.config = yaml.load(file, SafeLoader)
        if self.config is None:
            self.logger.log_error('Unable to read config file')

    def list_backups(self):
        return self.config['backups'].keys()

    def get_full_config(self):
        return self.config

    def get_backup_config(self, backup):
        return self.config['backups'][backup]

    def get_loggers_config(self):
        if 'loggers' in self.config:
            return self.config['loggers']
        else:
            return []


def load_yaml(filename, logger):
    config = Configuration(logger)
    config.load_yaml(filename)
    return config


def process_includes(backup_config, full_config):
    append_merger = deepmerge.Merger(
        [(list, ["append"]), (dict, ["merge"])], "use_existing", "use_existing")
    prepend_merger = deepmerge.Merger(
        [(list, ["prepend"]), (dict, ["merge"])], "use_existing", "use_existing")
    includes = backup_config.pop('includes', [])
    included = None
    for include in includes:
        new = None
        try:
            new = full_config['backups'][include]
        except KeyError:
            pass
        try:
            new = full_config['templates'][include]
        except KeyError:
            pass
        if new is None:
            raise KeyError(
                "Included section '{}' not found in configuration file".format(include))
        if included is None:
            included = new
        else:
            included = append_merger.merge(included, new)
    if included is not None:
        backup_config = prepend_merger.merge(
            backup_config, process_includes(included, full_config))
    return backup_config
