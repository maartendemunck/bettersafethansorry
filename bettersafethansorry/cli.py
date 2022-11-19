import argparse
import bettersafethansorry.configuration as bsts_configuration
import bettersafethansorry.operation as bsts_operation
import logging
import os


logger = logging.getLogger(__name__)


def run():
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
    config = bsts_configuration.load_yaml(config_file)
    if config is None:
        logger.error("Unable to load config file '{}'".format(
            config_file))
        exit(2)

    # Initialise logger(s).
    # logging.basicConfig(level=logging.DEBUG)

    # Run command.
    if args.command.lower() == 'list':
        print('Configured backups: {}'.format(
            ', '.join(config.list_backups())))
    elif args.command.lower() == 'do':
        dry_run = True if args.dry_run else False
        if (args.backup is None):
            logger.error("No backup specified")
            exit(2)
        try:
            backup_config = config.get_backup_config(
                args.backup)
        except KeyError:
            logger.error(
                "Backup '{}' not found in config file".format(args.backup))
            exit(2)
        error = bsts_operation.run_backup(backup_config, dry_run)
        if error:
            logger.error(
                "Error(s) encountered while making backup '{}'".format(args.backup))
    else:
        logger.error("Unknown command '{}'".format(args.command))


if __name__ == '__main__':
    run()
