import os
import os.path
import subprocess


def isfile(host, filename):
    if host is not None:
        returncode = subprocess.run(
            ['ssh', host, 'test -f {}'.format(filename)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        exists = True if returncode == 0 else False
    else:
        exists = os.path.isfile(filename)
    return exists


def remove(host, filename):
    if host is not None:
        returncode = subprocess.run(
            ['ssh', host, 'rm {}'.format(filename)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        success = True if returncode == 0 else False
    else:
        try:
            os.remove(filename)
            success = True
        except:
            success = False
    return success


def rename(host, filename_old, filename_new):
    if host is not None:
        returncode = subprocess.run(
            ['ssh', host, 'mv {} {}'.format(filename_old, filename_new)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        success = True if returncode == 0 else False
    else:
        try:
            os.replace(filename_old, filename_new)
            success = True
        except:
            success = False
    return success


def rotate_file(host, filename, tmp_suffix, keep, logger):
    errors = []
    keep = int(keep)
    logger.log_debug("Rotating archives")
    if isfile(host, filename + tmp_suffix):
        success = True
        # Delete last files.
        if isfile(host, filename + '.{}'.format(keep)):
            filename_old = filename + '.{}'.format(keep)
            logger.log_debug("Removing {}".format(filename_old))
            success &= remove(host, filename_old)
        # Move old files.
        for number in range(keep, 0, -1):
            filename_old = filename + \
                ('.{}'.format(number - 1) if (number - 1) > 0 else '')
            filename_new = filename + '.{}'.format(number)
            if isfile(host, filename_old):
                logger.log_debug("Renaming {} to {}".format(filename_old, filename_new))
                success &= rename(host, filename_old, filename_new)
        # Replace destination file by temporary file.
        filename_old = filename + tmp_suffix
        filename_new = filename
        logger.log_debug("Renaming {} to {}".format(filename_old, filename_new))
        success &= rename(host, filename_old, filename_new)
        # Log errors.
        if not success:
            logger.log_error("Unable to rotate file '{}'".format(filename))
            errors.append("Unable to rotate file '{}'".format(filename))
    else:
        # Log error if temporary file doesn't exist.
        logger.log_error("Temporary file '{}' doesn't exist, not rotating files".format(filename + tmp_suffix))
        errors.append("Temporary file '{}' doesn't exist, not rotating files".format(filename + tmp_suffix))
    return errors
