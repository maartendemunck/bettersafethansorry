import datetime
import logging
import sys


class MasterLogger:

    def __call_all_loggers(self, function_name, *args):
        timestamp = datetime.datetime.utcnow()
        for logger in self.loggers:
            function = getattr(logger, function_name)
            function(timestamp, *args)

    def __init__(self):
        # Configure and add a Python logging logger.
        self.loggers = [PythonLoggingLogger(logging.getLogger('BSTS'))]
        logging.basicConfig(level=logging.DEBUG, handlers=[])
        # Configure a Python logging streamhandler to log INFO messages to stderr.
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.add_logging_handler(console_handler)

    def add_logger(self, logger_config):
        errors = []
        logger_type = logger_config.pop('logger', None)
        if logger_type.lower() == 'file':
            filename = logger_config.pop('filename', None)
            if filename is None:
                self.log_message(
                    logging.ERROR, "No filename specified for 'File' logger")
                errors.append("No filename specified for 'File' logger")
            append = logger_config.pop('append', True)
            file_handler = logging.FileHandler(
                filename, 'a' if append else 'w')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname).1s %(message)s', '%Y-%m-%d %H:%M:%S'))
            self.add_logging_handler(file_handler)
        else:
            self.log_message(
                logging.ERROR, "Unknown logger '{}'".format(logger_type))
            errors.append("Unknown logger '{}'".format(logger_type))
        return errors

    def add_logging_handler(self, handler):
        self.loggers[0].get_python_logging_logger().addHandler(handler)

    def start_backup(self, id, description):
        self.__call_all_loggers('start_backup', id, description)

    def finish_backup(self, id, errors):
        self.__call_all_loggers('finish_backup', id, errors)

    def start_action(self, id, description):
        self.__call_all_loggers('start_action', id, description)

    def finish_action(self, id, errors):
        self.__call_all_loggers('finish_action', id, errors)

    def log_message(self, level, message):
        self.__call_all_loggers('log_message', level, message)


class PythonLoggingLogger:

    def __init__(self, python_logging_logger):
        self.logger = python_logging_logger

    def start_backup(self, timestamp, id, description):
        if description is not None and len(description) > 0:
            self.log_message(timestamp, logging.INFO,
                             "Starting backup '{}'".format(description))
        else:
            self.log_message(timestamp, logging.INFO, 'Starting backup')

    def finish_backup(self, timestamp, id, errors):
        if errors is None or len(errors) == 0:
            self.log_message(timestamp, logging.INFO,
                             "Backup completed without errors")
        else:
            self.log_message(timestamp, logging.INFO,
                             "{} errors encountered while making backup".format(len(errors)))

    def start_action(self, timestamp, id, description):
        if description is not None and len(description) > 0:
            self.log_message(timestamp, logging.INFO,
                             "Starting action '{}'".format(description))
        else:
            self.log_message(timestamp, logging.INFO, 'Starting action')

    def finish_action(self, timestamp, id, errors):
        if errors is None or len(errors) == 0:
            self.log_message(timestamp, logging.INFO,
                             "Action completed without errors")
        else:
            self.log_message(timestamp, logging.INFO,
                             "{} errors encountered:".format(len(errors)))
            for error in errors:
                self.log_message(timestamp, logging.ERROR, error)

    def log_message(self, timestamp, level, message):
        self.logger.log(level, message)

    def get_python_logging_logger(self):
        return self.logger
