class Action:

    required_keys = []
    optional_keys = {
        'all-or-nothing': False
    }

    def __init__(self, action_config, logger, extra_required_keys=[], extra_optional_keys={}):
        self.logger = logger
        self.logger.log_debug(
            "Initialising '{}' action".format(self.__class__.__name__))
        self.config = {}
        # Check required keys (and raise a KeyError if they don't exist).
        required_keys = [*Action.required_keys, *extra_required_keys]
        for key in required_keys:
            if key in action_config:
                self.config[key] = action_config.pop(key)
            else:
                self.logger.log_error(
                    "Required parameter '{}' not specified in '{}' config".format(key, self.__class__.__name__))
                raise KeyError()
        # Set defaults for optional keys; ignore keys that were already processed as required keys.
        optional_keys = {**Action.optional_keys, **extra_optional_keys}
        for key in optional_keys:
            if key not in required_keys:
                self.config[key] = action_config.pop(key, optional_keys[key])
            else:
                pass
        # Warn for unrecognised keys.
        for key in action_config:
            logger.log_warning(
                "Ignoring unrecognised parameter '{}' in '{}' config".format(key, self.__class__.__name__))

    def has_do(self):
        return False

    def do(self):
        return ['Not implemented']

    def has_prepare(self):
        return False

    def prepare(self, dry_run):
        return ['Not implemented']

    def has_commit(self):
        return False

    def commit(self, dry_run):
        return ['Not implemented']

    def has_rollback(self):
        return False

    def rollback(self, dry_run):
        return ['Not implemented']

    def has_check(self):
        return False

    def check(self):
        return ['Not implemented']
