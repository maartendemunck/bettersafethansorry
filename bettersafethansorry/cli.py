import argparse
import bettersafethansorry.configuration as bsts_config
import logging
import os


logger = logging.getLogger(__name__)


def run():
    # logging.basicConfig(level=logging.DEBUG)

    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description='Better Safe Than Sorry. Custom backups made easy.')
    parser.add_argument(
        'command', help='Command')
    parser.add_argument(
        'target', nargs='?', help='Select backup to perform')
    parser.add_argument('-c', '--config', help='Select configuration file')
    parser.add_argument('-n', '--dry-run',
                        help='Only display actions', action='store_true')
    args = parser.parse_args()

    # Read configuration file.
    if args.config is not None:
        configuration_file = args.config
    else:
        configuration_file = os.path.expanduser('~/.config/bettersafethansorry/config.yaml')
    configuration = bsts_config.load_yaml(configuration_file)
    if configuration is None:
        logger.error("Unable to load configuration file '{}'".format(configuration_file))
        exit(2)

    # Initialise logger(s).

    # Run command.
    if args.command.lower() == 'list':
        print('Configured backups: {}'.format(', '.join(configuration.list_backups())))
    else:
        logger.error("Unknown command '{}'".format(args.command))


if __name__ == '__main__':
    run()
