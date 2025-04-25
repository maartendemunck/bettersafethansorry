import bettersafethansorry.utilities as bsts_utils
import datetime
import exif
import fnmatch
import os
import re
import shutil
import tempfile
from bettersafethansorry.actions import Action
from collections import defaultdict
from pathlib import Path



class CopyPhotosVideos(Action):

    required_keys = [
        'source-directory',
        'destination-directory',
        'files'
    ]

    optional_keys = {}

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         CopyPhotosVideos.required_keys, CopyPhotosVideos.optional_keys)

    def has_do(self):
        return True

    def do(self, dry_run):
        for dirpath, dirnames, filenames in os.walk(self.config['source-directory']):
            dirnames.sort()
            filenames_filtered = []
            for pattern in self.config['files']:
                filenames_filtered.extend(fnmatch.filter(filenames, pattern))
            filenames_filtered.sort()
            for filename in filenames_filtered:
                source_filepath = os.path.join(dirpath, filename)
                source_stat = os.stat(source_filepath)
                try:
                    with open(source_filepath, 'rb') as image_file:
                        exif_info = exif.Image(image_file)
                    timestamp = datetime.datetime.strptime(
                        exif_info.get('datetime_original'), '%Y:%m:%d %H:%M:%S')
                    timestamp_source = 'EXIF data'
                except:
                    # Use the timestamp of the source file if we're unable to read the EXIF data.
                    timestamp = datetime.datetime.fromtimestamp(
                        source_stat.st_mtime)
                    timestamp_source = 'file modification time'
                destination_dirpath = timestamp.strftime(
                    self.config['destination-directory'])
                destination_filepath = os.path.join(
                    destination_dirpath, filename)
                if (os.path.exists(destination_filepath)):
                    self.logger.log_debug('Skipping {}'.format(filename))
                else:
                    if not dry_run:
                        if not os.path.exists(destination_dirpath):
                            self.logger.log_debug(
                                'Creating directory {}'.format(destination_dirpath))
                            os.makedirs(destination_dirpath)
                        self.logger.log_info('Copying {} to {} (based on {})'.format(
                            filename, destination_dirpath, timestamp_source))
                        shutil.copyfile(source_filepath, destination_filepath)
                        os.utime(destination_filepath,
                                 (source_stat.st_atime, source_stat.st_mtime))
                    else:
                        self.logger.log_info(
                            'Dry run, skipping copying {} to {} (based on {})'.format(
                                filename, destination_dirpath, timestamp_source))
        return []


class ConvertAndMergeVideos(Action):

    required_keys = [
        'source-directory',
        'source-pattern',
        'destination-directory',
        'destination-pattern'
    ]

    optional_keys = {}

    def __init__(self, action_config, logger):
        super().__init__(action_config, logger,
                         ConvertAndMergeVideos.required_keys, ConvertAndMergeVideos.optional_keys)
    
    def has_do(self):
        return True

    def do(self, dry_run):
        errors = []
        source_pattern = re.compile(self.config['source-pattern'], re.IGNORECASE)
        # Dictionary to collect video files by their movie ID.
        video_groups = defaultdict(list)
        # Traverse the source directory tree.
        for root, dirs, files in os.walk(self.config['source-directory']):
            for file in sorted(files):
                match = source_pattern.match(file)
                if match:
                    key = (root, match.group("video_id"))
                    part = match.group("part") or '000'
                    video_groups[key].append((part, file))
        # Process the grouped video files.
        for (root, video_id), files in sorted(video_groups.items()):
            source_files = [os.path.join(root, fname) for _, fname in sorted(files)]
            source_stat = Path(source_files[0]).stat()
            source_isotime = datetime.datetime.fromtimestamp(source_stat.st_mtime).isoformat()
            # Determine common output path.
            relative_path = Path(root).relative_to(self.config['source-directory'])
            destination_directory = self.config['destination-directory'] / relative_path
            destination_filename = self.config['destination-pattern'].format(video_id=video_id)
            destination_path = destination_directory / destination_filename
            destination_path_tmp = destination_path.with_suffix('.tmp')
            # Generate the output file.
            if not os.path.isfile(destination_path):
                if not dry_run:
                    if not os.path.exists(destination_directory):
                        self.logger.log_debug(
                            'Creating directory {}'.format(destination_directory))
                        os.makedirs(destination_directory)
                    self.logger.log_info('Converting {} to {}'.format(
                        ' + '.join([fname for _, fname in sorted(files)]), destination_filename))
                    if len(source_files) == 1:
                        # Convert the video files using ffmpeg.
                        convert_cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                                       '-i', source_files[0],
                                       '-c:v', 'libx265', '-crf', '26', '-preset', 'slow', '-c:a', 'copy',
                                       '-f', 'mp4', '-metadata', f'creation_time="{source_isotime}',
                                       destination_path_tmp]
                        commands = [convert_cmd]
                        exit_codes, stdouts, stderrs = bsts_utils.run_processes(commands, None, self.logger)
                        # Process the output of the command.
                        cmd_errors = bsts_utils.log_subprocess_errors(commands, exit_codes, stdouts, stderrs, self.logger)
                        errors.extend(cmd_errors)
                        if len(cmd_errors) > 0:
                            bsts_utils.remove_file(None, destination_path_tmp)
                        else:
                            bsts_utils.rename_file(None, destination_path_tmp, destination_path)
                            os.utime(destination_path, (source_stat.st_atime, source_stat.st_mtime))
                    else:
                        # Create a temporary file with the input video files.
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                            temp_file.write('\n'.join([f"file '{f}'" for f in source_files]))
                            temp_file_path = temp_file.name
                        # Convert the video files using ffmpeg.
                        convert_cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                                       '-safe', '0', '-f', 'concat', '-i', temp_file_path,
                                       '-c:v', 'libx265', '-crf', '26', '-preset', 'slow', '-c:a', 'copy',
                                       '-f', 'mp4',
                                       destination_path_tmp]
                        commands = [convert_cmd]
                        exit_codes, stdouts, stderrs = bsts_utils.run_processes(commands, None, self.logger)
                        # Process the output of the command.
                        cmd_errors = bsts_utils.log_subprocess_errors(commands, exit_codes, stdouts, stderrs, self.logger)
                        errors.extend(cmd_errors)
                        if len(cmd_errors) > 0:
                            bsts_utils.remove_file(None, destination_path_tmp)
                        else:
                            bsts_utils.rename_file(None, destination_path_tmp, destination_path)
                            os.utime(destination_path, (source_stat.st_atime, source_stat.st_mtime))
                        # Remove the temporary file.
                        bsts_utils.remove_file(None, temp_file_path)
                else:
                    self.logger.log_info(
                        'Dry run, skipping converting {} to {}'.format(
                            ' + '.join([fname for _, fname in sorted(files)]), destination_filename))
            else:
                self.logger.log_debug('Skipping {}'.format(destination_filename))
        return errors