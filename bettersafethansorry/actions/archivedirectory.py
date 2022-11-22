import re
import subprocess
import bettersafethansorry.actions as bsts_actions


class ArchiveDirectory:

    required_keys = (
        'source-directory',
        'destination-file')

    optional_keys = {
        'one-file-system': False,
        'source-host': None,
        'source-container': None,
        'source-compression': None,
        'compression': None,
        'destination-host': None,
        'destination-compression': None,
        'keep': 0
    }

    def __init__(self, action_config, logger):
        self.logger = logger
        self.logger.log_debug("Initialising 'ArchiveDirectory' action")
        self.config = {}
        # Check required keys (and raise a KeyError if they don't exist).
        for key in ArchiveDirectory.required_keys:
            if key in action_config:
                self.config[key] = action_config.pop(key)
            else:
                self.logger.log_error("Required parameter '{}' not specified in 'ArchiveDirectory' config".format(key))
                raise KeyError()
        # Set defaults for optional keys.
        for key in ArchiveDirectory.optional_keys:
            self.config[key] = action_config.pop(key, ArchiveDirectory.optional_keys[key])
        # Warn for unrecognised keys.
        for key in action_config:
            logger.log_warning("Ignoring unrecognised parameter '{}' in 'ArchiveDirectory' config".format(key))

    def has_do(self):
        return True

    def __compose_source_command(self):
        # Compose tar command.
        tar_cmd = [
            'tar',
            '--directory={}'.format(self.config['source-directory']),
            '--create',
            '--numeric-owner',
            '--acls',
            '--xattrs',
            *(['--one-file-system'] if self.config['one-file-system'] else []),
            '--sort=name',
            '--file=-',
            '.'
        ]
        # Compose docker command.
        if self.config['source-container'] is not None:
            user_container = re.fullmatch('((?P<user>.+)@)?(?P<container>[^@]+)', self.config['source-container'])
            if user_container is None:
                self.logger.log_warning("Invalid value for parameter 'source-container' in 'ArchiveDirectory' config")
                raise ValueError("Invalid value for parameter 'source-container' in 'ArchiveDirectory' config")
            user = user_container.groupdict()['user']
            container = user_container.groupdict()['container']
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
        cmd = tar_cmd
        if self.config['source-container'] is not None:
            cmd = docker_cmd + [' '.join(cmd)]
        if self.config['source-host'] is not None:
            if self.config['source-compression'] is not None:
                source_compression_cmd = ' | {}'.format(self.config['source-compression'])
            else:
                source_compression_cmd = ''
            cmd = ssh_command + [(' '.join(cmd) + source_compression_cmd)]
        return cmd

    def __compose_compression_command(self):
        if self.config['compression']:
            compression_cmd = self.config['compression'].split(' ')
        elif self.config['source-host'] is None and self.config['source-compression']:
            compression_cmd = self.config['source-compression'].split(' ')
        elif self.config['destination-host'] is None and self.config['destination-compression']:
            compression_cmd = self.config['destination-compression'].split(' ')
        else:
            compression_cmd = None
        return compression_cmd

    def __compose_destination_command(self):
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

    def __compose_destination_filename(self):
        if self.config['destination-host']:
            destination_filename = None
        else:
            destination_filename = \
                '{}.tmp'.format(self.config['destination-file'])
        return destination_filename

    def do(self, dry_run):
        self.logger.log_debug("Configuring 'ArchiveDirectory' action")
        # Create commands from action configuration.
        source_cmd = self.__compose_source_command()
        compression_cmd = self.__compose_compression_command()
        destination_cmd = self.__compose_destination_command()
        destination_filename = self.__compose_destination_filename()
        # Run commands.
        self.logger.log_debug("Executing 'ArchiveDirectory' action")
        errors = []
        if not dry_run:
            # Backup to temporary file.
            if destination_filename is not None:
                destination_file = open(destination_filename, "wb")
            else:
                destination_file = None
            processes = []
            processes.append(subprocess.Popen(
                source_cmd,
                stdin=None,
                stdout=subprocess.PIPE if compression_cmd is not None or destination_cmd is not None else destination_file,
                stderr=subprocess.PIPE))
            if compression_cmd is not None:
                processes.append(subprocess.Popen(
                    compression_cmd,
                    stdin=processes[-1].stdout,
                    stdout=subprocess.PIPE if destination_cmd is not None else destination_file,
                    stderr=subprocess.PIPE))
            if destination_cmd is not None:
                processes.append(subprocess.Popen(
                    destination_cmd,
                    stdin=processes[-1].stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE))
            exit_codes = []
            for process in processes:
                exit_codes.append(process.wait())
            error_output = ''
            for process in processes:
                (stdout, stderr) = process.communicate()
                error_output += stderr.decode('utf-8')
            if destination_file is not None:
                destination_file.close()
            if exit_codes[0] != 0:
                self.logger.log_error('Command exited with return code {}'.format(exit_codes[0]))
                for line in error_output.splitlines():
                    self.logger.log_error(line)
                    errors.append(line)
                # Remove temporary file.
                bsts_actions.remove(self.config['destination-host'], '{}.tmp'.format(self.config['destination-file']))
            else:
                # Rotate backup files.
                rotate_errors = bsts_actions.rotate_file(
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
