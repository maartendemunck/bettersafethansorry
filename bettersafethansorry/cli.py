import argparse
import bettersafethansorry.configuration as bsts_configuration
import bettersafethansorry.operation as bsts_operation
import bettersafethansorry.logging as bsts_logging
import errno
import os
import sys
import yaml


configuration = None
logger = None


def main():
    global configuration, logger

    try:
        configure_base_logger()
        command_line_arguments = parse_command_line_arguments()
        get_configuration(command_line_arguments)
        configure_additional_loggers()
    except Exception as exception:
        logger.log_error(f'An error occured during setup: "{exception}"')
        raise

    try:
        command = command_line_arguments.command.lower()
        if command == 'list':
            print_configured_backups()
            return_value = 0
        elif command == 'status':
            statuses = print_status_of_configured_backups()
            if len(statuses[True]) == 0 and len(statuses[None]) == 0:
                return_value = 0
            else:
                return_value = 127
        elif command == 'show':
            selected_backup = command_line_arguments.backup
            print_configuration_of_backup(selected_backup)
            return_value = 0
        elif command == 'do':
            selected_backup = command_line_arguments.backup
            run_only_when_outdated = True if command_line_arguments.auto else False
            dry_run = True if command_line_arguments.dry_run else False
            do_backup(selected_backup, run_only_when_outdated, dry_run)
            return_value = 0
        else:
            raise Exception(f'Unkown command "{command}"')
    except Exception as exception:
        logger.log_error(
            f'An error occured during command "{command}": "{exception}"')
        raise

    return return_value


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        description='Better Safe Than Sorry. Custom backups made easy.')
    parser.add_argument('command',
                        help="Command ('list', 'status', 'show' or 'do')")
    parser.add_argument('backup', nargs='?',
                        help="Select backup (for 'show' or 'do')")
    parser.add_argument('-c', '--config',
                        help='Select config file')
    parser.add_argument('-a', '--auto',
                        help="Only perform backup if it's outdated",
                        action='store_true')
    parser.add_argument('-n', '--dry-run',
                        help='Only display actions',
                        action='store_true')
    return parser.parse_args()


def get_configuration(command_line_arguments):
    global configuration
    if command_line_arguments.config is not None:
        config_file = command_line_arguments.config
    else:
        config_file = os.path.expanduser(
            '~/.config/bettersafethansorry/config.yaml')
    configuration = bsts_configuration.load_yaml(config_file, logger)
    if configuration is None:
        raise Exception(f'Unable to load configuration file "{config_file}"')


def configure_base_logger():
    global logger
    logger = bsts_logging.MasterLogger()


def configure_additional_loggers():
    global configuration, logger
    try:
        for logger_config in configuration.get_loggers_config():
            logger.add_logger(logger_config)
    except:
        raise Exception('Error(s) encountered while setting up loggers')


def print_configured_backups():
    global configuration
    print('Configured backups:')
    for backup, description in configuration.list_backups_and_descriptions().items():
        if description is not None:
            print(f'- {backup}: {description}')
        else:
            print(f'- {backup}')


def print_status_of_configured_backups():
    global configuration
    statuses = {None: [], False: [], True: []}
    status_strings = {None: ('No information available', '?'),
                      False: ('Up to date', '+'),
                      True: ('Outdated', '-')}
    for backup, description in configuration.list_backups_and_descriptions().items():
        status = logger.is_backup_outdated(backup)
        statuses[status].append((backup, description))
    for category in (None, False, True):
        if len(statuses[category]) > 0:
            category_decription = status_strings[category][0]
            print(f'{category_decription}:')
            for backup, description in statuses[category]:
                bullet_type = status_strings[category][1]
                if description is not None:
                    print(f'{bullet_type} {backup}: {description}')
                else:
                    print(f'{bullet_type} {backup}')
    return statuses


def get_postprocessed_backup_configuration(backup):
    global configuration
    if backup is None:
        raise Exception('No backup specified')
    try:
        backup_configuration = configuration.get_backup_config(backup)
        backup_configuration = bsts_configuration.process_includes(
            backup_configuration, configuration.get_full_config())
        backup_configuration = bsts_configuration.process_variables(
            backup_configuration)
        return backup_configuration
    except KeyError:
        raise Exception(f'Backup "{backup}" not found in configuration file')


def print_configuration_of_backup(backup):
    print()
    print(yaml.dump({backup: get_postprocessed_backup_configuration(backup)}))


def do_backup(backup, run_only_when_outdated, dry_run):
    global configuration, logger
    if run_only_when_outdated is False or logger.is_backup_outdated(backup) is not False:
        errors = bsts_operation.run_backup(
            backup, get_postprocessed_backup_configuration(backup), dry_run, logger)
        if errors is not None and len(errors) > 0:
            raise Exception(f'Error(s) encountered during backup: "{errors}"')


if __name__ == '__main__':
    sys.exit(main())
