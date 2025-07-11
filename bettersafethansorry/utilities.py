import os
import os.path
import re
import subprocess
import threading


def signal_first_last(iterable):
    iterator = iter(iterable)
    current_value = next(iterator)
    is_first = True
    for next_value in iterator:
        yield current_value, is_first, False
        current_value = next_value
        is_first = False
    yield current_value, is_first, True


def split_user_host(user_at_host, user_is_optional=False, host_is_optional=False):
    user_host = re.fullmatch(
        '((?P<user>[^@]+)@|@)?(?P<host>[^@]+)?', user_at_host)
    if user_host is None:
        raise ValueError(
            "Value '{}' not in 'user@host' format".format(user_at_host))
        return (None, None)
    else:
        user = user_host.groupdict()['user']
        host = user_host.groupdict()['host']
        if user is None and user_is_optional is False:
            raise ValueError(
                "Value '{}' requires but doesn't contain an username".format(user_at_host))
        if host is None and host_is_optional is False:
            raise ValueError(
                "Value '{}' requires but doesn't contain a hostname".format(user_at_host))
        return (user, host)


def split_user_password_host(user_password_host, user_is_optional=False, password_is_optional=False, host_is_optional=False):
    user_host = re.fullmatch(
        '((?P<user>[^@:]+)(:(?P<password>[^@:]*))?@|@)?(?P<host>[^@]+)?', user_password_host)
    if user_host is None:
        raise ValueError(
            "Value '{}' not in 'user@host' format".format(user_password_host))
        return (None, None, None)
    else:
        user = user_host.groupdict()['user']
        password = user_host.groupdict()['password']
        host = user_host.groupdict()['host']
        return (user, password, host)


def is_file(host, filename):
    if host is not None:
        returncode = subprocess.run(
            ['ssh', host, 'test -f {}'.format(filename)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        exists = True if returncode == 0 else False
    else:
        exists = os.path.isfile(filename)
    return exists


def remove_file(host, filename):
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


def rename_file(host, filename_old, filename_new):
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
    if is_file(host, filename + tmp_suffix):
        success = True
        # Delete last files.
        if is_file(host, filename + '.{}'.format(keep)):
            filename_old = filename + '.{}'.format(keep)
            logger.log_debug("Removing {}".format(filename_old))
            success &= remove_file(host, filename_old)
        # Move old files.
        for number in range(keep, 0, -1):
            filename_old = filename + \
                ('.{}'.format(number - 1) if (number - 1) > 0 else '')
            filename_new = filename + '.{}'.format(number)
            if is_file(host, filename_old):
                logger.log_debug("Renaming {} to {}".format(
                    filename_old, filename_new))
                success &= rename_file(host, filename_old, filename_new)
        # Replace destination file by temporary file.
        filename_old = filename + tmp_suffix
        filename_new = filename
        logger.log_debug("Renaming {} to {}".format(
            filename_old, filename_new))
        success &= rename_file(host, filename_old, filename_new)
        # Log errors.
        if not success:
            logger.log_error("Unable to rotate file '{}'".format(filename))
            errors.append("Unable to rotate file '{}'".format(filename))
    else:
        # Log error if temporary file doesn't exist.
        logger.log_error("Temporary file '{}' doesn't exist, not rotating files".format(
            filename + tmp_suffix))
        errors.append("Temporary file '{}' doesn't exist, not rotating files".format(
            filename + tmp_suffix))
    return errors


def run_processes(commands, stdout_filename, logger, cwd=None):

    def catch_stderr(index):
        # Do not use Popen.communicate because it also consumes part of
        # the stdout which should be received by the next subprocess.
        stderr = bytearray()
        for stderr_line in iter(processes[index].stderr.readline, b''):
            stderr.extend(stderr_line)
        processes[index].wait()
        exit_codes[index] = processes[index].returncode
        stderrs[index] = stderr.decode('utf-8') if stderr is not None else ''

    # Open output file if stdout of last process needs to be sent to a file.
    if stdout_filename is not None:
        stdout_file = open(stdout_filename, 'wb')
    else:
        stdout_file = None
    # Start processes.
    processes = []
    exit_codes = []
    stdouts = []
    stderrs = []
    threads = []
    for command, is_first, is_last in signal_first_last(commands):
        if cwd is None:
            logger.log_debug('Starting subprocess: {}'.format(command))
        else:
            logger.log_debug(
                "Starting subprocess: {} (cwd: '{}')".format(command, cwd))
        process_index = len(processes)
        processes.append(subprocess.Popen(
            command,
            stdin=processes[-1].stdout if not is_first else None,
            stdout=subprocess.PIPE if is_last is False else (
                stdout_file if stdout_filename is not None else
                subprocess.DEVNULL),
            stderr=subprocess.PIPE,
            cwd=cwd))
        exit_codes.append(None)
        stdouts.append(None)
        stderrs.append(None)
        thread = threading.Thread(target=catch_stderr, args=(process_index,))
        threads.append(thread)
        thread.start()
    # Wait for communicate threads to finish
    logger.log_debug("Waiting for subprocess(es) to finish")
    for thread in threads:
        thread.join()
    logger.log_debug("Subprocess(es) finished")
    # Close output file.
    if stdout_filename is not None:
        stdout_file.close()
    # Return all exit codes and stdout and stderr output.
    return exit_codes, stdouts, stderrs


def log_subprocess_errors(commands, exit_codes, stdouts, stderrs, logger):
    errors = []
    for command, exit_code, stdout, stderr in zip(commands, exit_codes, stdouts, stderrs):
        if exit_code == 0:
            logger.log_debug(
                "Subprocess '{}' exited successfully".format(command[0]))
        else:
            logger.log_error(
                "Subprocess '{}' exited with error code {}".format(' '.join(command), exit_code))
            if len(stderr) > 0:
                for line in stderr.splitlines():
                    logger.log_error(line)
                    errors.append(line)
            else:
                errors.append("No stderr output available")
    return errors
