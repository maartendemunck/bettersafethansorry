import argparse
import bettersafethansorry.configuration as bsts_configuration
import bettersafethansorry.operation as bsts_operation
import bettersafethansorry.loggers as bsts_loggers
import errno
import os
import sys


def run():
    # Configure the master logger.
    logger = bsts_loggers.MasterLogger()

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

    # Read and parse config file.
    if args.config is not None:
        config_file = args.config
    else:
        config_file = os.path.expanduser(
            '~/.config/bettersafethansorry/config.yaml')
    config = bsts_configuration.load_yaml(config_file, logger)
    if config is None:
        logger.log_error("Unable to load configuration file '{}'".format(config_file))
        sys.exit(errno.EINVAL)

    # Configure additional loggers.
    try:
        for logger_config in config.get_loggers_config():
            logger.add_logger(logger_config)
    except:
        logger.log_error("Error(s) encountered while setting up loggers")
        exit(errno.EINVAL)

    # Run command.
    if args.command.lower() == 'list':
        print('Configured backups: {}'.format(', '.join(config.list_backups())))
    elif args.command.lower() == 'do':
        dry_run = True if args.dry_run else False
        if (args.backup is None):
            logger.log_error("No backup specified")
            sys.exit(errno.EINVAL)
        try:
            backup_config = config.get_backup_config(args.backup)
        except KeyError:
            logger.log_error("Backup '{}' not found in config file".format(args.backup))
            sys.exit(errno.EINVAL)
        error = bsts_operation.run_backup(backup_config, dry_run, logger)
        if error is not None and len(error) > 0:
            exit(errno.EIO)
    else:
        logger.log_error("Unknown command '{}'".format(args.command))
        exit(errno.EINVAL)

    # Exit
    sys.exit(0)


if __name__ == '__main__':
    run()
