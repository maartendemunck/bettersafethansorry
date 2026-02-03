# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
