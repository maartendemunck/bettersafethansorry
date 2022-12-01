from bettersafethansorry.actions import Action
import bettersafethansorry.utilities as bsts_utils


class RsyncFiles(Action):

    required_keys = [
        'source-directory',
        'destination-directory'
    ]

    optional_keys = {
        'source-host': None,
        'destination-host': None,
        'follow-symlinks': False,
        'excludes': []
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         RsyncFiles.required_keys, RsyncFiles.optional_keys)

    def has_do(self):
        return True

    def _compose_rsync_command(self, use_shell):
        source = ''
        if self.config['source-host'] is not None:
            source += '{}:'.format(self.config['source-host'])
        source += self.config['source-directory']
        destination = ''
        if self.config['destination-host'] is not None and self.config['source_host'] is None:
            destination += '{}:'.format(self.config['destination-host'])
        destination += self.config['destination-directory']
        if use_shell is False:
            exclude_list = [
                "--exclude={}".format(excluded) for excluded in self.config['excludes']]
        else:
            exclude_list = ["--exclude='{}'".format(excluded.replace(
                "'", "\\'")) for excluded in self.config['excludes']]
        rsync_command = [
            'rsync',
            '--archive',
            '--timeout=120',
            '--delete',
            '--delete-excluded',
            *(exclude_list),
            *(['--copy-links'] if self.config['follow-symlinks'] else []),
            source,
            destination
        ]
        return rsync_command if use_shell is False else ' '.join(rsync_command)

    def _compose_command(self):
        if self.config['destination-host'] is not None and self.config['source_host'] is not None:
            return [
                'ssh',
                self.config['destination-host'],
                self._compose_rsync_command(True)
            ]
        else:
            return self._compose_rsync_command(False)

    def do(self, dry_run):
        self.logger.log_debug(
            "Configuring '{}' action".format(self.__class__.__name__))
        # Create commands from action configuration.
        commands = [self._compose_command()]
        # Run commands.
        self.logger.log_debug(
            "Executing '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                commands, None, self.logger)
            errors.extend(bsts_utils.log_subprocess_errors(
                commands, exit_codes, stdouts, stderrs, self.logger))
        else:
            self.logger.log_info('Dry run, skipping actions')
        return errors
