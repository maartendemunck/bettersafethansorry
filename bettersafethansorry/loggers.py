import datetime
import logging


class MasterLogger:

    def __call_all_loggers(self, function_name, *args):
        timestamp = datetime.datetime.utcnow()
        for logger in self.loggers:
            function = getattr(logger, function_name)
            function(timestamp, *args)

    def __init__(self):
        self.loggers = []

    def add_logger(self, logger):
        self.loggers.append(logger)

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
