import time
from bettersafethansorry.actions import Action
import bettersafethansorry.utilities as bsts_utils


class ArchiveStuff(Action):

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
        'keep': 0,
        'retry': 1
    }

    def __init__(self, action_config, logger, extra_required_keys=[], extra_optional_keys={}):
        required_keys = [*ArchiveStuff.required_keys, *extra_required_keys]
        optional_keys = {**ArchiveStuff.optional_keys, **extra_optional_keys}
        super().__init__(action_config, logger, required_keys, optional_keys)

    def _convert_command_to_string(self, command):
        if isinstance(command, list):
            command = ' '.join(command)
        return command

    def _compose_source_docker_command(self, source_container):
        run_archive_command_in_container = source_container is not None
        if run_archive_command_in_container:
            (user, container) = bsts_utils.split_user_host(
                source_container, True, False)
            docker_cmd = [
                'docker',
                'exec',
                *(['--user', user] if user is not None else []),
                container
            ]
        else:
            docker_cmd = []
        return docker_cmd

    def _compose_source_ssh_command(self, source_host):
        run_archive_command_in_ssh = source_host is not None
        if run_archive_command_in_ssh:
            ssh_command = [
                'ssh',
                source_host
            ]
        else:
            ssh_command = []
        return ssh_command

    def _compose_source_compression_command(self, source_compression):
        use_source_compression = source_compression is not None
        if use_source_compression:
            source_compression_cmd = ' | {}'.format(source_compression)
        else:
            source_compression_cmd = ''
        return source_compression_cmd

    def _compose_source_commands(self, source_commands_function, is_archive_function):
        source_container = self.config['source-container']
        run_archive_command_in_container = source_container is not None
        source_host = self.config['source-host']
        run_archive_command_in_ssh = source_host is not None
        run_archive_command_in_shell = (
            run_archive_command_in_container or run_archive_command_in_ssh)
        if is_archive_function:
            source_cmds = [source_commands_function(run_archive_command_in_shell)]
        else:
            source_cmds = source_commands_function(run_archive_command_in_shell)
        full_source_cmds = []
        for source_cmd in source_cmds:
            full_source_cmd = source_cmd
            if run_archive_command_in_container:
                docker_cmd = self._compose_source_docker_command(source_container)
                full_source_cmd = docker_cmd + [full_source_cmd]
            if run_archive_command_in_ssh:
                full_source_cmd = self._convert_command_to_string(full_source_cmd)
                ssh_command = self._compose_source_ssh_command(source_host)
                if is_archive_function:
                    source_compression = self.config['source-compression']
                else:
                    source_compression = None
                source_compression_cmd = self._compose_source_compression_command(source_compression)
                full_source_cmd = ssh_command + [full_source_cmd + source_compression_cmd]
            full_source_cmds.append(full_source_cmd)
        return full_source_cmds

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
                'ssh',
                self.config['destination-host'],
                cmd_string
            ]
        else:
            destination_cmd = None
        return destination_cmd

    def _compose_pre_archive_commands(self):
        if hasattr(self.__class__, '_compose_base_pre_archive_commands') and \
            callable(getattr(self.__class__, '_compose_base_pre_archive_commands')):
            return self._compose_source_commands(self._compose_base_pre_archive_commands, False)
        else:
            return []

    def _compose_archive_commands(self):
        source_cmd = self._compose_source_commands(self._compose_base_archive_command, True)[0]
        compression_cmd = self._compose_compression_command()
        destination_cmd = self._compose_destination_command()
        commands = [
            source_cmd,
            *([compression_cmd] if compression_cmd is not None else []),
            *([destination_cmd] if destination_cmd is not None else [])
        ]
        return commands

    def _compose_post_archive_commands(self):
        if hasattr(self.__class__, '_compose_base_post_archive_commands') and \
            callable(getattr(self.__class__, '_compose_base_post_archive_commands')):
            return self._compose_source_commands(self._compose_base_post_archive_commands, False)
        else:
            return []

    def _compose_destination_filename(self):
        if self.config['destination-host']:
            destination_filename = None
        else:
            destination_filename = \
                '{}.tmp'.format(self.config['destination-file'])
        return destination_filename

    def _do_pre_post_commands(self, commands, dry_run):
        errors = []
        if not dry_run:
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(commands, None, self.logger)
            errors = bsts_utils.log_subprocess_errors(commands, exit_codes, stdouts, stderrs, self.logger)
        else:
            # Show command that would be executed
            self.logger.log_info('Would run: {}'.format(' | '.join(map(' '.join, commands))))
        return errors

    def _do_archive_prepare(self, dry_run):
        """Execute archive commands to create .tmp file without rotating backups."""
        self.logger.log_debug(
            "Configuring '{}' action".format(self.__class__.__name__))
        commands = self._compose_archive_commands()
        destination_filename = self._compose_destination_filename()
        self.logger.log_debug(
            "Executing '{}' action (prepare phase)".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                commands, destination_filename, self.logger)
            errors.extend(bsts_utils.log_subprocess_errors(
                commands, exit_codes, stdouts, stderrs, self.logger))
        else:
            # Show command that would be executed
            if destination_filename:
                self.logger.log_info('Would run: {} > {}'.format(
                    ' | '.join(map(' '.join, commands)), destination_filename))
            else:
                self.logger.log_info('Would run: {}'.format(
                    ' | '.join(map(' '.join, commands))))
        return errors

    def _do_archive_commit(self, dry_run):
        """Rotate backup files after successful prepare."""
        self.logger.log_debug(
            "Committing '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
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
            # Show what would be committed
            self.logger.log_info('Would rotate: {}.tmp -> {} (keeping {} old versions)'.format(
                self.config['destination-file'],
                self.config['destination-file'],
                self.config['keep']))
        return errors

    def _do_archive_rollback(self, dry_run):
        """Remove temporary file after failed prepare."""
        self.logger.log_debug(
            "Rolling back '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            bsts_utils.remove_file(
                self.config['destination-host'],
                '{}.tmp'.format(self.config['destination-file']))
        else:
            # Show what would be rolled back
            self.logger.log_info('Would remove: {}.tmp'.format(
                self.config['destination-file']))
        return errors

    def _do_archive_commands(self, dry_run):
        self.logger.log_debug(
            "Configuring '{}' action".format(self.__class__.__name__))
        commands = self._compose_archive_commands()
        destination_filename = self._compose_destination_filename()
        self.logger.log_debug(
            "Executing '{}' action".format(self.__class__.__name__))
        errors = []
        if not dry_run:
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                commands, destination_filename, self.logger)
            errors.extend(bsts_utils.log_subprocess_errors(
                commands, exit_codes, stdouts, stderrs, self.logger))
            if len(errors) > 0:
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
            # Show command that would be executed
            if destination_filename:
                self.logger.log_info('Would run: {} > {}'.format(
                    ' | '.join(map(' '.join, commands)), destination_filename))
            else:
                self.logger.log_info('Would run: {}'.format(
                    ' | '.join(map(' '.join, commands))))
        return errors

    def do(self, dry_run):
        self._assure_do_function_is_implemented()
        retry = self.config['retry']
        successful = False
        while (not successful) and retry > 0:
            errors = []
            # Prepare phase
            prepare_errors = self.prepare(dry_run)
            errors.extend(prepare_errors)

            # Commit or rollback based on success
            if len(prepare_errors) == 0:
                commit_errors = self.commit(dry_run)
                errors.extend(commit_errors)
            else:
                rollback_errors = self.rollback(dry_run)
                errors.extend(rollback_errors)

            retry -= 1
            if len(errors) > 0:
                if retry > 0:
                    self.logger.log_info('Errors encountered during action; retrying action...')
                else:
                    self.logger.log_error('Errors encountered during action but no retries left.')
            else:
                successful = True
        return errors

    def _assure_do_function_is_implemented(self):
        if not self.has_do():
            raise NotImplementedError(
                "'{}' action doesn't support 'do' command".format(self.__class__.__name__))
        return

    def has_prepare(self):
        return True

    def prepare(self, dry_run):
        """Prepare phase: run pre-commands and create archive .tmp file."""
        errors = []
        for pre_archive_command in self._compose_pre_archive_commands():
            pre_archive_errors = self._do_pre_post_commands([pre_archive_command], dry_run)
            errors.extend(pre_archive_errors)
        archive_errors = self._do_archive_prepare(dry_run)
        errors.extend(archive_errors)
        return errors

    def has_commit(self):
        return True

    def commit(self, dry_run):
        """Commit phase: rotate backup files and run post-commands."""
        errors = []
        commit_errors = self._do_archive_commit(dry_run)
        errors.extend(commit_errors)
        for post_archive_command in self._compose_post_archive_commands():
            post_archive_errors = self._do_pre_post_commands([post_archive_command], dry_run)
            errors.extend(post_archive_errors)
        return errors

    def has_rollback(self):
        return True

    def rollback(self, dry_run):
        """Rollback phase: remove .tmp file."""
        errors = []
        rollback_errors = self._do_archive_rollback(dry_run)
        errors.extend(rollback_errors)
        return errors

    def has_verify(self):
        return True

    def _get_decompression_command(self):
        """Get the decompression command based on config.

        Returns the decompression command (e.g., 'gunzip -c', 'bunzip2 -c')
        or None if no compression is used.
        """
        # Use the same logic as backup to determine compression
        compression = None
        if self.config['destination-compression']:
            compression = self.config['destination-compression']
        elif self.config['compression']:
            compression = self.config['compression']
        elif self.config['source-compression']:
            compression = self.config['source-compression']

        if compression is None:
            return None

        # Map compression commands to decompression commands
        compression_lower = compression.lower()
        if 'gzip' in compression_lower or compression_lower.startswith('gz'):
            return 'gunzip -c'
        elif 'bzip2' in compression_lower or 'bz2' in compression_lower:
            return 'bunzip2 -c'
        elif 'xz' in compression_lower:
            return 'xz -dc'
        else:
            # Unknown compression, try to infer from the command
            return None

    def _compose_file_exists_command(self):
        """Compose a command to check if backup file exists."""
        destination_file = self.config['destination-file']
        return 'test -f {}'.format(destination_file)

    def _compose_verify_commands(self):
        """Compose verify commands, wrapping with SSH if needed.

        Returns list of command lists suitable for run_processes.
        """
        destination_host = self.config['destination-host']

        # Get the base verify command from subclass
        verify_cmd = self._compose_base_verify_command()

        if destination_host:
            return [['ssh', destination_host, verify_cmd]]
        else:
            return [['sh', '-c', verify_cmd]]

    def verify(self, dry_run):
        """Verify backup integrity by checking file exists and validating compression."""
        self.logger.log_debug(
            "Verifying '{}' action".format(self.__class__.__name__))
        errors = []
        destination_file = self.config['destination-file']
        destination_host = self.config['destination-host']
        location = '{}:{}'.format(destination_host, destination_file) if destination_host else destination_file

        if not dry_run:
            # Step 1: Check if file exists
            exists_cmd = self._compose_file_exists_command()
            if destination_host:
                exists_command = ['ssh', destination_host, exists_cmd]
            else:
                exists_command = ['sh', '-c', exists_cmd]

            exit_codes, _, _ = bsts_utils.run_processes(
                [exists_command], None, self.logger)
            if exit_codes[0] != 0:
                error_msg = 'Backup file does not exist: {}'.format(location)
                self.logger.log_error(error_msg)
                errors.append(error_msg)
                return errors

            self.logger.log_info('Backup file exists: {}'.format(location))

            # Step 2: Verify archive integrity
            verify_commands = self._compose_verify_commands()
            self.logger.log_info('Verifying integrity of {}'.format(location))
            exit_codes, stdouts, stderrs = bsts_utils.run_processes(
                verify_commands, None, self.logger)
            errors.extend(bsts_utils.log_subprocess_errors(
                verify_commands, exit_codes, stdouts, stderrs, self.logger))

            if len(errors) == 0:
                self.logger.log_info('Archive integrity verified: {}'.format(location))
        else:
            # Show commands that would be executed
            exists_cmd = self._compose_file_exists_command()
            if destination_host:
                self.logger.log_info('Would run: ssh {} {}'.format(destination_host, exists_cmd))
            else:
                self.logger.log_info('Would run: {}'.format(exists_cmd))

            verify_commands = self._compose_verify_commands()
            self.logger.log_info('Would run: {}'.format(' '.join(verify_commands[0])))

        return errors


class ArchiveFiles(ArchiveStuff):

    required_keys = [
        'source-directory'
    ]

    optional_keys = {
        'one-file-system': False,
        'follow-symlinks': False,
        'excludes': [],
        'minimalistic-tar': False
    }

    def __init__(self, action_config, logger, extra_required_keys=[], extra_optional_keys={}):
        required_keys = [*ArchiveFiles.required_keys, *extra_required_keys]
        optional_keys = {**ArchiveFiles.optional_keys, **extra_optional_keys}
        super().__init__(action_config, logger, required_keys, optional_keys)

    def has_do(self):
        return True

    def _compose_base_archive_command(self, use_shell):
        # Compose tar command.
        if use_shell is False:
            directory = '--directory={}'.format(
                self.config['source-directory'])
            exclude_list = [
                "--exclude={}".format(excluded) for excluded in self.config['excludes']]
        else:
            directory = "--directory='{}'".format(
                self.config['source-directory'])
            exclude_list = ["--exclude='{}'".format(excluded.replace(
                "'", "\\'")) for excluded in self.config['excludes']]
        tar_cmd = [
            'tar',
            *([directory]),
            *(exclude_list),
            '--create',
            '--numeric-owner',
            *(['--acls', '--xattrs'] if not self.config['minimalistic-tar'] else []),
            *(['--one-file-system'] if self.config['one-file-system'] else []),
            *(['--sort=name'] if not self.config['minimalistic-tar'] else []),
            *(['--dereference'] if self.config['follow-symlinks']
              and not self.config['minimalistic-tar'] else []),
            '--file=-',
            '.'
        ]
        return tar_cmd if use_shell is False else self._convert_command_to_string(tar_cmd)

    def _compose_base_verify_command(self):
        """Compose tar archive verification command."""
        destination_file = self.config['destination-file']
        decompression = self._get_decompression_command()

        if decompression:
            return '{} {} | tar -t > /dev/null'.format(decompression, destination_file)
        else:
            return 'tar -tf {} > /dev/null'.format(destination_file)


class ArchiveMySQL(ArchiveStuff):

    required_keys = [
        'source-database'
    ]

    optional_keys = {
    }

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         ArchiveMySQL.required_keys, ArchiveMySQL.optional_keys)

    def has_do(self):
        return True

    def _compose_base_archive_command(self, use_shell):
        # Compose pg_dump command.
        (user, password, database) = bsts_utils.split_user_password_host(
            self.config['source-database'], True, True, True)
        mysqldump_cmd = [
            'mysqldump',
            *(['--user={}'.format(user)] if user is not None else []),
            *(['--password={}'.format(password)]
              if password is not None and use_shell is False else []),
            *(["--password='{}'".format(password)]
              if password is not None and use_shell is True else []),
            '--triggers',
            '--routines',
            '--events',
            '{}'.format(database),
        ]
        return mysqldump_cmd if use_shell is False else self._convert_command_to_string(mysqldump_cmd)

    def _compose_base_verify_command(self):
        """Compose SQL dump verification command (decompression test only)."""
        destination_file = self.config['destination-file']
        decompression = self._get_decompression_command()

        if decompression:
            # Decompress and discard output - verifies integrity
            return '{} {} > /dev/null'.format(decompression, destination_file)
        else:
            # Uncompressed file - just check it's readable
            return 'test -r {}'.format(destination_file)


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

    def _compose_base_archive_command(self, use_shell):
        # Compose pg_dump command.
        (user, database) = bsts_utils.split_user_host(
            self.config['source-database'], True, False)
        pgdump_cmd = [
            'pg_dump',
            '{}'.format(database),
            *(['--username={}'.format(user)] if user is not None else []),
            '--no-password'
        ]
        return pgdump_cmd if use_shell is False else self._convert_command_to_string(pgdump_cmd)

    def _compose_base_verify_command(self):
        """Compose SQL dump verification command (decompression test only)."""
        destination_file = self.config['destination-file']
        decompression = self._get_decompression_command()

        if decompression:
            # Decompress and discard output - verifies integrity
            return '{} {} > /dev/null'.format(decompression, destination_file)
        else:
            # Uncompressed file - just check it's readable
            return 'test -r {}'.format(destination_file)
