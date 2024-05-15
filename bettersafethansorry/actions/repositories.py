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

    def _compose_sync_command(self):
        git_annex_command = [
            'git',
            'annex',
            'sync',
            '--no-resolvemerge',
            '--no-content',
            *(self.config['remotes'])
        ]
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

    def _compose_get_command(self):
        git_annex_command = [
            'git',
            'annex',
            'get',
            '--auto'
        ]
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
        else:
            self.logger.log_info('Dry run, skipping actions')
        return errors
