from bettersafethansorry.actions import Action
import bettersafethansorry.utilities as bsts_utils


class UpdateGitAnnex(Action):

    required_keys = [
        'destination-directory'
    ]

    optional_keys = {
        'destination-host': None,
        'remotes': []
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         UpdateGitAnnex.required_keys, UpdateGitAnnex.optional_keys)

    def has_do(self):
        return True

    def _wrap_command_with_ssh(self, git_annex_command):
        """Wrap a git-annex command with SSH if destination-host is configured.

        Returns:
            tuple: (command, cwd) where command is the final command list and cwd is
                   the working directory (None if using SSH, directory path otherwise)
        """
        if self.config['destination-host'] is not None:
            ssh_command = [
                'ssh',
                self.config['destination-host'],
                'cd {} && {}'.format(self.config['destination-directory'],
                                     ' '.join(git_annex_command))
            ]
            return (ssh_command, None)
        else:
            return (git_annex_command, self.config['destination-directory'])

    def _compose_sync_command(self):
        git_annex_command = [
            'git',
            'annex',
            'sync',
            '--no-resolvemerge',
            '--no-content',
            *(self.config['remotes'])
        ]
        return self._wrap_command_with_ssh(git_annex_command)

    def _compose_get_command(self):
        git_annex_command = [
            'git',
            'annex',
            'get',
            '--auto'
        ]
        return self._wrap_command_with_ssh(git_annex_command)

    def do(self, dry_run):
        self.logger.log_debug(
            "Configuring '{}' action".format(self.__class__.__name__))
        # Create commands from action configuration.
        # Run commands.
        self.logger.log_debug(
            "Executing '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            # git annex sync
            command, cwd = self._compose_sync_command()
            commands = [command]
            try:
                exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                    commands, None, self.logger, cwd=cwd)
                errors.extend(bsts_utils.log_subprocess_errors(
                    commands, exit_codes, stdouts, stderrs, self.logger))
                if exit_codes[0] == 0:
                    # git annex get
                    command, cwd = self._compose_get_command()
                    commands = [command]
                    exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                        commands, None, self.logger, cwd=cwd)
                    errors.extend(bsts_utils.log_subprocess_errors(
                        commands, exit_codes, stdouts, stderrs, self.logger))
            except FileNotFoundError as e:
                self.logger.log_error(str(e))
                errors.append(str(e))
        else:
            # Show commands that would be executed
            sync_command, sync_cwd = self._compose_sync_command()
            self.logger.log_info('Would run: {}{}'.format(
                ' '.join(sync_command),
                ' (in {})'.format(sync_cwd) if sync_cwd else ''))
            get_command, get_cwd = self._compose_get_command()
            self.logger.log_info('Would run: {}{}'.format(
                ' '.join(get_command),
                ' (in {})'.format(get_cwd) if get_cwd else ''))
        return errors

    def has_verify(self):
        return True

    def _compose_fsck_command(self):
        git_annex_command = [
            'git',
            'annex',
            'fsck',
            '--quiet',
            '--numcopies=1'
        ]
        return self._wrap_command_with_ssh(git_annex_command)

    def verify(self, dry_run):
        self.logger.log_debug(
            "Verifying '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            # git annex fsck
            command, cwd = self._compose_fsck_command()
            commands = [command]
            try:
                exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                    commands, None, self.logger, cwd=cwd)
                errors.extend(bsts_utils.log_subprocess_errors(
                    commands, exit_codes, stdouts, stderrs, self.logger))
            except FileNotFoundError as e:
                self.logger.log_error(str(e))
                errors.append(str(e))
        else:
            # Show command that would be executed
            command, cwd = self._compose_fsck_command()
            self.logger.log_info('Would run: {}{}'.format(
                ' '.join(command),
                ' (in {})'.format(cwd) if cwd else ''))
        return errors
