import uuid
from bettersafethansorry.actions.archive import ArchiveFiles, ArchivePostgreSQL, ArchiveMySQL
from bettersafethansorry.actions.dcim import CopyPhotosVideos, ConvertAndMergeVideos
from bettersafethansorry.actions.rsync import RsyncFiles
from bettersafethansorry.actions.repositories import UpdateGitAnnex
from bettersafethansorry.actions.minecraft import ArchiveMinecraftServerJavaEdition


def run_backup(backup_name, backup_config, dry_run, logger):
    description = backup_config.pop('description', '')
    id = uuid.uuid4()
    logger.start_backup(id, backup_name, description)

    errors = []
    for action_config in backup_config['actions']:
        action_errors = run_backup_action(action_config, dry_run, logger)
        errors.extend(action_errors)

    logger.finish_backup(id, errors)
    return errors


def run_backup_action(action_config, dry_run, logger):
    description = action_config.pop('description', '')
    id = uuid.uuid4()
    logger.start_action(id, description)

    try:
        action_class = globals()[action_config.pop('action')]
    except KeyError as error:
        raise RuntimeError("Unknown action {}".format(error)) from error

    action_instance = action_class(action_config, logger)
    errors = action_instance.do(dry_run)

    logger.finish_action(id, errors)
    return errors
