import logging
from bettersafethansorry.actions.archivedirectory import ArchiveDirectory


logger = logging.getLogger(__name__)


def run_backup(backup_config, dry_run):
    error = False
    for action_config in backup_config:
        error |= run_backup_action(action_config, dry_run)
    return error


def run_backup_action(action_config, dry_run):
    action_class = globals()[action_config.pop('action')]
    action_instance = action_class(action_config, logger)
    error = action_instance.do(dry_run)
    return error
