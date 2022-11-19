import subprocess


class ArchiveDirectory:

    required_keys = (
        'source-directory',
        'destination-file')

    optional_keys = {
        'one-file-system': False,
        'source-host': None,
        'source-compression': None,
        'compression': None,
        'destination-host': None,
        'destination-compression': None,
        'keep': None
    }

    def __init__(self, action_config, logger):
        self.logger = logger
        self.logger.info('Initialising ArchiveDirectory')
        self.config = action_config
        for key in ArchiveDirectory.required_keys:
            if key not in action_config:
                logger.error(
                    "Required parameter '{}' not specified for 'ArchiveDirectory'".format(key))
                raise KeyError()
        for key in ArchiveDirectory.optional_keys:
            if key not in action_config:
                action_config[key] = ArchiveDirectory.optional_keys[key]

    def has_do(self):
        return True

    def do(self, dry_run):
        # Create source command (tar + ssh for remote sources).
        self.logger.debug("Configuring 'ArchiveDirectory' action")
        tar_cmd = [
            '/usr/bin/tar',
            '--directory={}'.format(self.config['source-directory']),
            '--create',
            '--numeric-owner',
            '--acls',
            '--xattrs',
            *('--one-file-system' for _i in range(1)
              if self.config['one-file-system']),
            '--sort=name',
            '--file=-',
            '.'
        ]
        if self.config['source-host']:
            cmd_string = ' '.join(tar_cmd)
            if self.config['source-compression']:
                cmd_string += ' | {}'.format(
                    self.config['source-compression'])
            source_cmd = [
                '/usr/bin/ssh',
                self.config['source-host'],
                cmd_string
            ]
        else:
            source_cmd = tar_cmd
        # Create local compression command.
        if self.config['compression']:
            compression_cmd = self.config['compression'].split(' ')
        elif self.config['source-host'] is None and self.config['source-compression']:
            compression_cmd = self.config['source-compression'].split(' ')
        elif self.config['destination-host'] is None and self.config['destination-compression']:
            compression_cmd = self.config['destination-compression'].split(' ')
        else:
            compression_cmd = None
        # Create destination commmand.
        if self.config['destination-host']:
            cmd_string = 'cat'
            if self.config['destination-compression']:
                cmd_string += ' | {}'.format(
                    self.config['destination-compression'])
            # TODO: write to temp file first
            cmd_string += ' > {}'.format(self.config['destination-file'])
            destination_cmd = [
                '/usr/bin/ssh',
                self.config['destination-host'],
                cmd_string
            ]
            destination_filename = None
        else:
            destination_cmd = None
            # TODO: write to temp file first
            destination_filename = self.config['destination-file']
        # Run commands.
        if not dry_run:
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
            (stdout, stderr) = processes[-1].communicate()
            exit_code = processes[0].wait()
            if destination_file is not None:
                destination_file.close()
            return False if exit_code == 0 else True
        else:
            cmd_string = ' '.join(source_cmd)
            if compression_cmd is not None:
                cmd_string += ' | ' + ' '.join(compression_cmd)
            if destination_cmd is not None:
                cmd_string += ' | ' + ' '.join(destination_cmd)
            if destination_filename is not None:
                cmd_string += ' > {}'.format(destination_filename)
            print(cmd_string)
            return False
        # Done.

    def has_check(self):
        return False

    def check(self):
        return False
