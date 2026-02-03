# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-03

### Added

- **Verify functionality** for backup validation
  - New `verify` CLI command to verify backup integrity
  - New `has_verify()` and `verify(dry_run)` methods in Action base class
  - Implemented verification for UpdateGitAnnex action using `git annex fsck --quiet --numcopies=1`
  - Full logger support with `start_verify()` and `finish_verify()` methods:
    - Added to Logger base class interface
    - Implemented in MasterLogger to broadcast to all loggers
    - Implemented in PythonLogger with appropriate log messages
    - Implemented in ApiRegistrar to register verifications with type='verify'
  - New `run_verify()` function in operation.py that processes all actions supporting verification
  - Verification skips actions that don't implement `has_verify()` (with debug logging)
  - Supports `--dry-run` flag to preview verification operations

- **Usage examples and documentation**
  - Added verification usage examples to README showing basic and dry-run usage
  - Documented exit codes (0 for success, 1 for failure) for both backup and verify commands
  - Documented what verification checks (missing files, checksums, repository consistency)

### Changed

- **Improved exit codes**
  - Both `do` and `verify` commands now return proper exit codes:
    - Exit code 0: Operation successful (no errors)
    - Exit code 1: Operation failed (errors encountered)
  - Changed from raising exceptions to returning exit codes for better scriptability
  - Added error count logging: "Backup failed with N error(s)" / "Verification failed with N error(s)"

- **Enhanced dry-run output across all action types**
  - **UpdateGitAnnex**: Shows exact commands with working directory
    - `Would run: git annex sync --no-resolvemerge --no-content`
    - `Would run: git annex get --auto`
    - `Would run: git annex fsck --quiet --numcopies=1`
  - **RsyncFiles**: Shows complete rsync command with all flags
    - `Would run: rsync --archive --timeout=120 --delete ...`
  - **ArchiveStuff** (and all archive actions): Shows detailed operation information
    - `Would run: tar ... | bzip2 > file.tar.bz2.tmp`
    - `Would rotate: file.tar.bz2.tmp -> file.tar.bz2 (keeping 3 old versions)`
    - `Would remove: file.tar.bz2.tmp`
  - **CopyPhotosVideos**: Shows copy operations with timestamps
    - `Would copy: photo.jpg -> /path/to/2024-01-15 (based on EXIF data)`
  - **ConvertAndMergeVideos**: Shows ffmpeg command with all parameters
    - `Would run: ffmpeg -y -hide_banner -loglevel error -i input.mp4 ...`
  - Changed from generic "Skipping..." messages to specific "Would run:" / "Would copy:" / "Would rotate:" messages

- **Refactored SSH wrapper logic in UpdateGitAnnex**
  - Extracted duplicated SSH command wrapping into `_wrap_command_with_ssh()` helper method
  - Now used by `_compose_sync_command()`, `_compose_get_command()`, and new `_compose_fsck_command()`
  - Eliminates code duplication and improves maintainability

- **ApiRegistrar logger improvements**
  - Refactored `finish_backup()` to use new `_register_operation()` helper method
  - Reduces duplication between backup and verification registration
  - Tracks verifications separately in `self.verifications` dictionary

### Technical Details

- Verify operations follow the same logging pattern as backup operations
- Actions can independently implement verification without affecting other functionality
- The verify command processes actions sequentially (no all-or-nothing logic needed)
- CLI help text updated to include 'verify' command
- Dry-run mode now provides actionable information for testing and debugging configurations

## [0.2.0] - 2026-02-03

### Added

- **All-or-nothing transaction support** for consistent multi-action backups
  - New `all-or-nothing: true` configuration flag for actions
  - Actions with this flag are grouped together and use two-phase commit semantics:
    - **Prepare phase**: All actions create temporary `.tmp` backup files
    - **Commit phase**: If all preparations succeed, all backups are committed together (files rotated)
    - **Rollback phase**: If any preparation fails, all temporary files are cleaned up
  - Ensures consistent backups across multiple filesystems or databases from the same point in time
  - Prevents partial backup sets where some filesystems are up-to-date while others remain at older versions

### Changed

- Split `ArchiveStuff` action logic into three distinct phases:
  - `prepare()`: Creates backup archive to temporary file
  - `commit()`: Rotates backup files and finalizes the backup
  - `rollback()`: Removes temporary files on failure
- Updated `Action` base class with new methods:
  - `has_prepare()`, `prepare(dry_run)`
  - `has_commit()`, `commit(dry_run)`
  - `has_rollback()`, `rollback(dry_run)`
- Refactored main backup loop in `operation.py`:
  - Separates actions into all-or-nothing and regular groups
  - Processes regular actions with existing `do()` method
  - Processes all-or-nothing actions with new two-phase commit logic
- Improved logging for all-or-nothing actions:
  - "Preparing action 'description'" instead of generic "Starting action"
  - "Action prepared without errors" for successful preparation
  - "Committing action 'description'" reuses original action description
  - "Action committed without errors" for successful commit
  - "Rolling back action 'description'" for cleanup on failure
- Optimized prepare phase to skip remaining actions after first failure
  - Logs "Skipping action 'description' (previous action failed)" for clarity
  - Only actions that were prepared are rolled back

### Technical Details

- All-or-nothing actions support is implemented at the `ArchiveStuff` level, making it available to:
  - `ArchiveFiles`
  - `ArchivePostgreSQL`
  - `ArchiveMySQL`
- The `do()` method now internally uses prepare/commit/rollback for backward compatibility
- Actions without the flag continue to work exactly as before
- Partial .tmp files are always cleaned up, even if the tar command is interrupted

### Documentation

- Updated README.md with all-or-nothing example in wormwood-image backup configuration
- Added explanation of how the feature works and its benefits
- Updated roadmap to mark feature as implemented

## [0.1.0] - Previous versions

- Initial release with core backup functionality
- Support for various backup types (files, PostgreSQL, MySQL, git-annex, photos/videos)
- Configuration system with YAML format, templates, and variable substitution
- Command line interface with list, status, show, and do commands
- Logging system with file and console output
- Automatic backup scheduling and outdated backup warnings
