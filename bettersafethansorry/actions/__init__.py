class Action:

    required_keys = []
    optional_keys = {}

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
        # Set defaults for optional keys.
        optional_keys = {**Action.optional_keys, **extra_optional_keys}
        for key in optional_keys:
            self.config[key] = action_config.pop(key, optional_keys[key])
        # Warn for unrecognised keys.
        for key in action_config:
            logger.log_warning(
                "Ignoring unrecognised parameter '{}' in '{}' config".format(key, self.__class__.__name__))

    def has_do(self):
        return False

    def do(self):
        return ['Not implemented']

    def has_check(self):
        return False

    def check(self):
        return ['Not implemented']
