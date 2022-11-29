import uuid
from bettersafethansorry.actions.archive import ArchiveFiles, ArchivePostgreSQL
from bettersafethansorry.actions.rsync import RsyncFiles
from bettersafethansorry.actions.repositories import UpdateGitAnnex


def run_backup(backup_config, dry_run, logger):
    description = backup_config.pop('description', '')
    id = uuid.uuid4()
    logger.start_backup(id, description)

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

    action_class = globals()[action_config.pop('action')]
    action_instance = action_class(action_config, logger)
    errors = action_instance.do(dry_run)

    logger.finish_action(id, errors)
    return errors
