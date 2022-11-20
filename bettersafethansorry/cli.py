import argparse
import bettersafethansorry.configuration as bsts_configuration
import bettersafethansorry.operation as bsts_operation
import bettersafethansorry.loggers as bsts_loggers
import logging
import os
import sys


def run():
    # Configure a (Python logging) logger.
    logging.basicConfig(level=logging.DEBUG, handlers=[])
    python_logger = logging.getLogger('BSTS')
    # Configure a (Python logging) handler to INFO messages to the console
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    python_logger.addHandler(console_handler)
    # Create the master logger and add the Python logging logger with the console handler to it.
    logger = bsts_loggers.MasterLogger()
    logger.add_logger(bsts_loggers.PythonLoggingLogger(python_logger))

    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description='Better Safe Than Sorry. Custom backups made easy.')
    parser.add_argument(
        'command', help='Command')
    parser.add_argument(
        'backup', nargs='?', help='Select backup to perform')
    parser.add_argument('-c', '--config', help='Select config file')
    parser.add_argument('-n', '--dry-run',
                        help='Only display actions', action='store_true')
    args = parser.parse_args()

    # Read config file.
    if args.config is not None:
        config_file = args.config
    else:
        config_file = os.path.expanduser(
            '~/.config/bettersafethansorry/config.yaml')
    config = bsts_configuration.load_yaml(config_file, logger)
    if config is None:
        exit(2)

    # Run command.
    if args.command.lower() == 'list':
        print(
            'Configured backups: {}'.format(', '.join(config.list_backups())))
    elif args.command.lower() == 'do':
        dry_run = True if args.dry_run else False
        if (args.backup is None):
            logger.log_message(logging.ERROR, "No backup specified")
            exit(2)
        try:
            backup_config = config.get_backup_config(args.backup)
        except KeyError:
            logger.log_message(
                logging.ERROR, "Backup '{}' not found in config file".format(args.backup))
            exit(2)
        error = bsts_operation.run_backup(backup_config, dry_run, logger)
        if error:
            logger.log_message(
                logging.ERROR, "Error(s) encountered while making backup '{}'".format(args.backup))
    else:
        logger.log_message(
            logging.ERROR, "Unknown command '{}'".format(args.command))


if __name__ == '__main__':
    run()
