from bettersafethansorry.actions import Action
import bettersafethansorry.utilities as bsts_utils


class RsyncFiles(Action):

    required_keys = [
        'source-directory',
        'destination-directory'
    ]

    optional_keys = {
        'source-host': None,
        'source-container': None,
        'destination-host': None,
        'follow-symlinks': False,
        'optimize-renames': False,
        'preserve-ownership': True,
        'fake-super': False,
        'excludes': []
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         RsyncFiles.required_keys, RsyncFiles.optional_keys)
        if self.config['source-container'] is not None and self.config['source-host'] is None:
            self.logger.log_error(
                "'source-container' requires 'source-host' to be set in '{}' config".format(
                    self.__class__.__name__))
            raise ValueError(
                "'source-container' requires 'source-host' to be set")

    def has_do(self):
        return True

    def _compose_source_rsync_path(self):
        source_container = self.config['source-container']
        if source_container is None:
            return None
        (user, container) = bsts_utils.split_user_host(
            source_container, True, False)
        docker_cmd = [
            'docker',
            'exec',
            '-i',
            *(['--user', user] if user is not None else []),
            container,
            'rsync'
        ]
        return ' '.join(docker_cmd)

    def _compose_rsync_command(self, use_shell):
        source = ''
        if self.config['source-host'] is not None:
            source += '{}:'.format(self.config['source-host'])
        source += self.config['source-directory']
        destination = ''
        if self.config['destination-host'] is not None and self.config['source-host'] is None:
            destination += '{}:'.format(self.config['destination-host'])
        destination += self.config['destination-directory']
        if use_shell is False:
            exclude_list = [
                "--exclude={}".format(excluded) for excluded in self.config['excludes']]
        else:
            exclude_list = ["--exclude='{}'".format(excluded.replace(
                "'", "\\'")) for excluded in self.config['excludes']]
        rsync_path = self._compose_source_rsync_path()
        if rsync_path is None:
            rsync_path_arg = []
        elif use_shell is False:
            rsync_path_arg = ['--rsync-path={}'.format(rsync_path)]
        else:
            rsync_path_arg = ["--rsync-path='{}'".format(rsync_path)]
        rsync_command = [
            'rsync',
            '--archive',
            '--timeout=120',
            '--delete',
            '--delete-excluded',
            *(exclude_list),
            *(rsync_path_arg),
            *(['--copy-links'] if self.config['follow-symlinks'] else []),
            *(['--fuzzy', '--delete-delay', '--delay-updates']
              if self.config['optimize-renames'] else []),
            *(['--no-owner', '--no-group']
              if not self.config['preserve-ownership'] else []),
            *(['--fake-super'] if self.config['fake-super'] else []),
            source,
            destination
        ]
        return rsync_command if use_shell is False else ' '.join(rsync_command)

    def _compose_command(self):
        if self.config['destination-host'] is not None and self.config['source-host'] is not None:
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
            # Show command that would be executed
            command = self._compose_command()
            self.logger.log_info('Would run: {}'.format(' '.join(command)))
        return errors
