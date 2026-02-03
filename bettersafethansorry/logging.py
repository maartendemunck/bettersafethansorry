import datetime
import logging
import sys
from bettersafethansorry.loggers import Logger
from bettersafethansorry.loggers.api import ApiRegistrar


class MasterLogger:

    def __init__(self):
        # Configure and add a Python logging logger.
        self.loggers = [PythonLogger(logging.getLogger('BSTS'))]
        logging.basicConfig(level=logging.DEBUG, handlers=[])
        # Configure a Python logging streamhandler to log INFO messages to stderr.
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.add_logging_handler(console_handler)

    def add_logger(self, logger_config):
        logger_type = logger_config.pop('logger', None)
        if logger_type.lower() == 'file':
            filename = logger_config.pop('filename', None)
            if filename is None:
                self.log_error("No filename specified for 'File' logger")
                raise KeyError("No filename specified for 'File' logger")
            append = logger_config.pop('append', True)
            file_handler = logging.FileHandler(
                filename, 'a' if append else 'w')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname).1s %(message)s', '%Y-%m-%d %H:%M:%S'))
            self.add_logging_handler(file_handler)
        else:
            try:
                logger_class = globals()[logger_type]
            except:
                self.log_error("Unknown logger type '{}'".format(logger_type))
                raise ValueError(
                    "Unknown logger type '{}'".format(logger_type))
            try:
                logger_instance = logger_class(logger_config, self)
            except:
                self.log_error(
                    "Unable to configure logger '{}'".format(logger_type))
                raise ValueError(
                    "Unable to configure logger '{}'".format(logger_type))
            self.loggers.append(logger_instance)

    def add_logging_handler(self, handler):
        self.loggers[0].get_python_logging_logger().addHandler(handler)

    def _call_all_loggers(self, function_name, *args):
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        for logger in self.loggers:
            function = getattr(logger, function_name)
            function(timestamp, *args)

    def start_backup(self, id, name, description):
        self._call_all_loggers('start_backup', id, name, description)

    def finish_backup(self, id, errors):
        self._call_all_loggers('finish_backup', id, errors)

    def start_verify(self, id, name, description):
        self._call_all_loggers('start_verify', id, name, description)

    def finish_verify(self, id, errors):
        self._call_all_loggers('finish_verify', id, errors)

    def start_action(self, id, description):
        self._call_all_loggers('start_action', id, description)

    def finish_action(self, id, errors):
        self._call_all_loggers('finish_action', id, errors)

    def log_message(self, level, message):
        self._call_all_loggers('log_message', level, message)

    def log_error(self, message):
        self.log_message(logging.ERROR, message)

    def log_warning(self, message):
        self.log_message(logging.WARNING, message)

    def log_info(self, message):
        self.log_message(logging.INFO, message)

    def log_debug(self, message):
        self.log_message(logging.DEBUG, message)

    def is_backup_outdated(self, name):
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        outdated = None
        for logger in self.loggers:
            outdated = outdated or logger.is_backup_outdated(timestamp, name)
        return outdated


class PythonLogger(Logger):

    def __log_info(self, timestamp, message):
        self.log_message(timestamp, logging.INFO, message)

    def __init__(self, python_logging_logger):
        self.logger = python_logging_logger

    def start_backup(self, timestamp, id, name, description):
        if description is not None and len(description) > 0:
            self.__log_info(
                timestamp, "Starting backup '{}'".format(description))
        else:
            self.__log_info(timestamp, 'Starting backup')

    def finish_backup(self, timestamp, id, errors):
        if errors is None or len(errors) == 0:
            self.__log_info(timestamp, 'Backup completed without errors')
        else:
            self.__log_info(timestamp, 'Error(s) encountered during backup')

    def start_verify(self, timestamp, id, name, description):
        if description is not None and len(description) > 0:
            self.__log_info(
                timestamp, "Starting verification '{}'".format(description))
        else:
            self.__log_info(timestamp, 'Starting verification')

    def finish_verify(self, timestamp, id, errors):
        if errors is None or len(errors) == 0:
            self.__log_info(timestamp, 'Verification completed without errors')
        else:
            self.__log_info(timestamp, 'Error(s) encountered during verification')

    def start_action(self, timestamp, id, description):
        if description is not None and len(description) > 0:
            self.__log_info(
                timestamp, "Starting action '{}'".format(description))
        else:
            self.__log_info(timestamp, 'Starting action')

    def finish_action(self, timestamp, id, errors):
        if errors is None or len(errors) == 0:
            self.__log_info(timestamp, 'Action completed without errors')
        else:
            self.__log_info(timestamp, 'Error(s) encountered during action')

    def log_message(self, timestamp, level, message):
        self.logger.log(level, message)

    def get_python_logging_logger(self):
        return self.logger
