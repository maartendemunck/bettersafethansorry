import bettersafethansorry.utilities as bsts_utils


class ArchiveStuff:

    required_keys = [
        'destination-file'
    ]

    optional_keys = {
        'source-host': None,
        'source-container': None,
        'source-compression': None,
        'compression': None,
        'destination-host': None,
        'destination-compression': None,
        'keep': 0
    }

    def __init__(self, action_config, logger, extra_required_keys=[], extra_optional_keys={}):
        self.logger = logger
        self.logger.log_debug(
            "Initialising '{}' action".format(self.__class__.__name__))
        self.config = {}
        # Check required keys (and raise a KeyError if they don't exist).
        required_keys = [*ArchiveStuff.required_keys, *extra_required_keys]
        for key in required_keys:
            if key in action_config:
                self.config[key] = action_config.pop(key)
            else:
                self.logger.log_error(
                    "Required parameter '{}' not specified in '{}' config".format(key, self.__class__.__name__))
                raise KeyError()
        # Set defaults for optional keys.
        optional_keys = {**ArchiveStuff.optional_keys, **extra_optional_keys}
        for key in optional_keys:
            self.config[key] = action_config.pop(key, optional_keys[key])
        # Warn for unrecognised keys.
        for key in action_config:
            logger.log_warning(
                "Ignoring unrecognised parameter '{}' in '{}' config".format(key, self.__class__.__name__))

    def has_do(self):
        return False

    def _compose_source_command(self):
        archive_cmd = self._compose_archive_command()
        # Compose docker command.
        if self.config['source-container'] is not None:
            (user, container) = bsts_utils.split_user_at_host(
                self.config['source-container'], True, False)
            docker_cmd = [
                'docker',
                'exec',
                *(['--user', user] if user is not None else []),
                container
            ]
        # Compose ssh command.
        if self.config['source-host'] is not None:
            ssh_command = [
                'ssh',
                self.config['source-host']
            ]
        # Compose full command.
        cmd = archive_cmd
        if self.config['source-container'] is not None:
            cmd = docker_cmd + [' '.join(cmd)]
        if self.config['source-host'] is not None:
            if self.config['source-compression'] is not None:
                source_compression_cmd = ' | {}'.format(
                    self.config['source-compression'])
            else:
                source_compression_cmd = ''
            cmd = ssh_command + [(' '.join(cmd) + source_compression_cmd)]
        return cmd

    def _compose_compression_command(self):
        if self.config['compression']:
            compression_cmd = self.config['compression'].split(' ')
        elif self.config['source-host'] is None and self.config['source-compression']:
            compression_cmd = self.config['source-compression'].split(' ')
        elif self.config['destination-host'] is None and self.config['destination-compression']:
            compression_cmd = self.config['destination-compression'].split(' ')
        else:
            compression_cmd = None
        return compression_cmd

    def _compose_destination_command(self):
        if self.config['destination-host']:
            cmd_string = 'cat'
            if self.config['destination-compression']:
                cmd_string += ' | {}'.format(
                    self.config['destination-compression'])
            cmd_string += ' > {}.tmp'.format(self.config['destination-file'])
            destination_cmd = [
                '/usr/bin/ssh',
                self.config['destination-host'],
                cmd_string
            ]
        else:
            destination_cmd = None
        return destination_cmd

    def _compose_destination_filename(self):
        if self.config['destination-host']:
            destination_filename = None
        else:
            destination_filename = \
                '{}.tmp'.format(self.config['destination-file'])
        return destination_filename

    def do(self, dry_run):
        if not self.has_do():
            raise NotImplementedError(
                "'{}' action doesn't support 'do' command".format(self.__class__.__name__))
        self.logger.log_debug(
            "Configuring '{}' action".format(self.__class__.__name__))
        # Create commands from action configuration.
        source_cmd = self._compose_source_command()
        compression_cmd = self._compose_compression_command()
        destination_cmd = self._compose_destination_command()
        destination_filename = self._compose_destination_filename()
        commands = [
            source_cmd,
            *([compression_cmd] if compression_cmd is not None else []),
            *([destination_cmd] if destination_cmd is not None else [])
        ]
        # Run commands.
        self.logger.log_debug(
            "Executing '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(commands, destination_filename)
            if exit_codes[0] != 0:
                self.logger.log_error(
                    'Command exited with return code {}'.format(exit_codes[0]))
                for line in stdouts[0].splitlines():
                    self.logger.log_error(line)
                    errors.append(line)
                # Remove temporary file.
                bsts_utils.remove_file(
                    self.config['destination-host'], '{}.tmp'.format(self.config['destination-file']))
            else:
                # Rotate backup files.
                rotate_errors = bsts_utils.rotate_file(
                    self.config['destination-host'],
                    self.config['destination-file'],
                    '.tmp',
                    self.config['keep'],
                    self.logger)
                for error in rotate_errors:
                    self.logger.log_error(error)
                errors.extend(rotate_errors)
        else:
            self.logger.log_info('Dry run, skipping actions')
        return errors

    def has_check(self):
        return False

    def check(self):
        return ['Not implemented']


class ArchiveDirectory(ArchiveStuff):

    required_keys = [
        'source-directory'
    ]

    optional_keys = {
        'one-file-system': False,
        'minimalistic-tar': False
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         ArchiveDirectory.required_keys, ArchiveDirectory.optional_keys)

    def has_do(self):
        return True

    def _compose_archive_command(self):
        # Compose tar command.
        tar_cmd = [
            'tar',
            '--directory={}'.format(self.config['source-directory']),
            '--create',
            '--numeric-owner',
            *(['--acls', '--xattrs'] if not self.config['minimalistic-tar'] else []),
            *(['--one-file-system'] if self.config['one-file-system'] else []),
            *(['--sort=name'] if not self.config['minimalistic-tar'] else []),
            '--file=-',
            '.'
        ]
        return tar_cmd


class ArchivePostgreSQL(ArchiveStuff):

    required_keys = [
        'source-database'
    ]

    optional_keys = {
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         ArchivePostgreSQL.required_keys, ArchivePostgreSQL.optional_keys)

    def has_do(self):
        return True

    def _compose_archive_command(self):
        # Compose pg_dump command.
        (user, database) = bsts_utils.split_user_at_host(
            self.config['source-database'], True, False)
        pgdump_cmd = [
            'pg_dump',
            '{}'.format(database),
            *(['--username={}'.format(user)] if user is not None else [])
        ]
        return pgdump_cmd
