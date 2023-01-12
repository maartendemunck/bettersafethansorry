import datetime
import exif
import fnmatch
import os
import shutil
from bettersafethansorry.actions import Action


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
                with open(source_filepath, 'rb') as image_file:
                    exif_info = exif.Image(image_file)
                timestamp = datetime.datetime.strptime(
                    exif_info.get('datetime_original'), '%Y:%m:%d %H:%M:%S')
                destination_dirpath = timestamp.strftime(
                    self.config['destination-directory'])
                destination_filepath = os.path.join(
                    destination_dirpath, filename)
                if (os.path.exists(destination_filepath)):
                    self.logger.log_debug('Skipping {}'.format(filename))
                else:
                    if not dry_run:
                        self.logger.log_info('Copying {} to {}'.format(
                            filename, destination_dirpath))
                        if not os.path.exists(destination_dirpath):
                            self.logger.log_debug(
                                'Creating directory {}'.format(destination_dirpath))
                            os.makedirs(destination_dirpath)
                        shutil.copyfile(source_filepath, destination_filepath)
                        os.utime(destination_filepath,
                                 (source_stat.st_atime, source_stat.st_mtime))
                    else:
                        self.logger.log_info('Dry run, skipping copying {} to {}'.format(
                            filename, destination_dirpath))
        return []
