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

    # Separate actions into all-or-nothing and regular groups
    all_or_nothing_actions = []
    regular_actions = []

    for action_config in backup_config['actions']:
        if action_config.get('all-or-nothing', False):
            all_or_nothing_actions.append(action_config)
        else:
            regular_actions.append(action_config)

    # Process regular actions (call do() directly)
    for action_config in regular_actions:
        action_errors = run_backup_action(action_config, dry_run, logger)
        errors.extend(action_errors)

    # Process all-or-nothing actions (prepare/commit/rollback)
    if len(all_or_nothing_actions) > 0:
        aon_errors = run_all_or_nothing_actions(
            all_or_nothing_actions, dry_run, logger)
        errors.extend(aon_errors)

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


def run_all_or_nothing_actions(action_configs, dry_run, logger):
    """Execute a group of actions with all-or-nothing semantics.

    All actions are prepared first. If all preparations succeed, all are committed.
    If any preparation fails, all are rolled back.
    """
    errors = []
    action_data = []  # Store (action_instance, description) tuples

    # Phase 1: Prepare all actions
    logger.log_info('Starting prepare phase of all-or-nothing action group')
    prepare_errors = []
    prepare_failed = False

    for action_config in action_configs:
        description = action_config.pop('description', '')

        # If a previous action failed, skip remaining preparations
        if prepare_failed:
            logger.log_info("Skipping action '{}' (previous action failed)".format(
                description) if description else "Skipping action (previous action failed)")
            continue

        # Custom logging for prepare phase
        logger.log_info("Preparing action '{}'".format(
            description) if description else "Preparing action")

        try:
            action_class = globals()[action_config.pop('action')]
        except KeyError as error:
            raise RuntimeError("Unknown action {}".format(error)) from error

        action_instance = action_class(action_config, logger)

        # Check if action supports all-or-nothing
        if not (action_instance.has_prepare() and action_instance.has_commit() and action_instance.has_rollback()):
            error_msg = "'{}' action does not support 'all-or-nothing' mode".format(
                action_instance.__class__.__name__)
            logger.log_error(error_msg)
            prepare_errors.append(error_msg)
            prepare_failed = True
            continue

        # Execute prepare phase
        action_prepare_errors = action_instance.prepare(dry_run)
        prepare_errors.extend(action_prepare_errors)

        # Always add to action_data so it gets rolled back if needed
        action_data.append((action_instance, description))

        # Log completion of prepare phase
        if len(action_prepare_errors) == 0:
            logger.log_info('Action prepared without errors')
        else:
            logger.log_error('Error(s) encountered during action preparation')
            prepare_failed = True

    # Phase 2: Commit or rollback based on prepare results
    if len(prepare_errors) == 0:
        # All preparations succeeded - commit all
        logger.log_info('All preparations succeeded, committing all actions')
        for action_instance, description in action_data:
            # Custom logging for commit phase
            logger.log_info("Committing action '{}'".format(
                description) if description else "Committing action")

            commit_errors = action_instance.commit(dry_run)
            errors.extend(commit_errors)

            # Log completion of commit phase
            if len(commit_errors) == 0:
                logger.log_info('Action committed without errors')
            else:
                logger.log_error('Error(s) encountered during action commit')
    else:
        # At least one preparation failed - rollback all
        logger.log_error(
            'One or more preparations failed, rolling back all actions')
        errors.extend(prepare_errors)
        for action_instance, description in action_data:
            # Custom logging for rollback phase
            logger.log_info("Rolling back action '{}'".format(
                description) if description else "Rolling back action")

            rollback_errors = action_instance.rollback(dry_run)

            # Log completion of rollback phase
            if len(rollback_errors) == 0:
                logger.log_info('Action rolled back without errors')
            else:
                logger.log_error('Error(s) encountered during action rollback')
            # Don't add rollback errors to main error list to avoid double-counting

    return errors


def run_verify(backup_name, backup_config, dry_run, logger):
    """Verify a backup configuration by running verify() on all actions that support it.

    Args:
        backup_name: Name of the backup configuration
        backup_config: Configuration dictionary containing actions
        dry_run: If True, show what would be verified without executing
        logger: Logger instance for logging messages

    Returns:
        list: List of error messages (empty if no errors)
    """
    description = backup_config.pop('description', '')
    id = uuid.uuid4()
    logger.start_verify(id, backup_name, description)

    errors = []

    # Process all actions that support verification
    for action_config in backup_config['actions']:
        action_description = action_config.pop('description', '')
        action_id = uuid.uuid4()

        try:
            action_class = globals()[action_config.pop('action')]
        except KeyError as error:
            raise RuntimeError("Unknown action {}".format(error)) from error

        action_instance = action_class(action_config, logger)

        # Only verify actions that implement verification
        if action_instance.has_verify():
            logger.start_action(action_id, action_description)
            action_errors = action_instance.verify(dry_run)
            errors.extend(action_errors)
            logger.finish_action(action_id, action_errors)
        else:
            # Skip actions that don't support verification
            logger.log_debug(
                "Skipping verification for action '{}' (not implemented)".format(
                    action_description) if action_description else "Skipping verification for action (not implemented)")

    logger.finish_verify(id, errors)
    return errors
