# Better Safe Than Sorry

Custom backups made easy.

Copyright (C) 2022-2025 Maarten De Munck (<maarten@vijfendertig.be>).

## About Better Safe Than Sorry

I have quite some Linux systems at home which contain various types of data ranging from normal files, git (and some old svn) repositories, databases to the git-annex repository which I use to store my full archive. Some of this data is quite important for me, so a reliable backup strategy is imperative.

I started with a simple shell script copying important files to external USB drives a long time ago (in 2014, according to my git history). Over time, I collected a large number of shell functions for all different types of data and a lot of code to call the right functions for every possible backup. And functions to verify backups of course, since a corrupted backup is even more frustrating than no backup at all.

To make things a bit easier to maintain, I started writing Better Safe Than Sorry. The main goal is to create a library of my backup functions, a system to configure all my backups and a way to run the backups, either manually (for backups from and to mobile devices) or automatic (from and to remote systems).

## Installation

## Getting Started

To decrease my electricity consumption, I recently bought a mini server (wormwood) to run some applications that previously ran on my desktop PC (calvin) so that I can just shut down my desktop PC when I'm not using it. This system currently runs my maarten@home website with some webapps (and some other services, but let's keep the example small) in Docker containers and is the perfect example to show how Better Safe Than Sorry works.

The most important data on this system are of course the data (database and media files) of my maarten@home website (and the data of the other services). The website itself and the deployment scripts of the website and other services are stored in Git repositories, so no additional data backups are needed. To reduce the recovery time in case the the SSD or the full system would fail, I want to make a full system backup now and then, but this takes a lot more time and no data is lost if this backup is a bit outdated, so I split the data and system backups.

These requirements yield this configuration file `~/.config/bettersafethansorry/config.yaml` for Better Safe Than Sorry:

```yaml
backups:
  wormwood-image:
    description: Full filesystem backup of Wormwood
    actions:
      - description: Backup / filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /
        destination-host: maarten@calvin.home.vijfendertig.be
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-root.tar.bz2
        destination-compression: /usr/bin/bzip2 -9
        keep: 3
        excludes:
          - ./sys
      - description: Backup /boot filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /boot/
        destination-host: maarten@calvin.home.vijfendertig.be
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-boot.tar.bz2
        destination-compression: /usr/bin/bzip2 -9
        keep: 3
      - description: Backup /boot/efi filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /boot/efi/
        destination-host: maarten@calvin.home.vijfendertig.be
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-efi.tar.bz2
        destination-compression: /usr/bin/bzip2 -9
        keep: 3
  wormwood-maartenathome:
    description: maarten@home website data
    actions:
      - description: Archive maarten@home django database
        action: ArchivePostgreSQL
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: maartenathome-maartenathome-postgres-1
        source-database: maartenathome@maartenathome
        destination-file: /srv/backup/hosts/wormwood/data/maartenathome-database.sql.bz2
        destination-compression: bzip2
        keep: 3
      - description: Archive maarten@home django media
        action: ArchiveFiles
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: django@maartenathome-maartenathome-django-1
        source-directory: /srv/django/media/
        destination-file: /srv/backup/hosts/wormwood/data/maartenathome-media.tar.bz2
        destination-compression: bzip2
        keep: 3
loggers:
  - logger: File
    filename: /home/maarten/.local/log/bettersafethansorry.log
    append: true
```

The configuration file defines three backups:

- `wormwood-image` makes a full filesystem backup, split in one `.tar.bz2` archive for each filesystem (`/`, `/boot` and `/boot/efi`). The backups are made to my desktop PC and because I have a decent LAN at home and the CPU of my desktop PC is much more performant than the CPU of the mini server, I send the backups as (uncompressed) tar files to my desktop PC and bzip2 them there. The `all-or-nothing: true` flag ensures that all three filesystem backups are consistent: all backups are first prepared (creating temporary `.tmp` files), and only if all preparations succeed are the backups committed (rotating old backups and moving `.tmp` files to their final names). If any preparation fails, all temporary files are rolled back, ensuring you never have a mix of old and new backups from different points in time.
- `wormwood-maartenathome` makes a backup of the Django database in the maarten@home PostgreSQL container and the data directory in the maarten@home Django container. The backups are made to whatever system runs the backup (the data is important and the backup is not that big, so I sometimes just backup to my laptop if my desktop is off). Again, compression is done on the system running the backup.

Logs are stored in a simple text file `~/.local/log/bettersafethansorry.log` and subsequent invocations just add their logs to the file.

`bsts list` lists the available backups. `bsts status` lists all backups and shows which backups are outdated.

`bsts do wormwood-image` and `bsts do wormwood-maartenathome` run the individual backups.

`bsts verify wormwood-image` and `bsts verify wormwood-maartenathome` verify the backups. This functionality is currently only supported for git-annex archives, which it will check for:
- Missing or corrupted files
- Checksum mismatches
- Repository consistency

Both backups (do) and verification (verify) return exit code 0 on success or 1 if errors are found.

## Usage

### Command Line Interface

Usage: `bsts [-h] [-c CONFIG] [-n] command [backup]`

Positional arguments:

- `command`: `list`, `status`, `show`, `do` or `verify`
- `backup`: backup to show, perform or verify (as defined in the configuration file)

Options:

- `-h` or `--help`: show this help message and exit
- `-c CONFIG` or `--config CONFIG`: select configuration file
- `-a` or `--auto`: only perform the backup if it is outdated
- `-n` or `--dry-run`: do not actually perform actions, only log them

### Configuration file

## Roadmap

Backup functions:

- [X] Rsync files and directories, both local and remote
- [X] Archive files, directories and filesystems, both local and remote, both native and in a docker container
- [X] Backup PostgreSQL databases, both local and remote, both native and in a docker container
- [X] Backup MySQL and MariaDB databases, both local and remote, both native and in a docker container
- [X] Backup Git-annex repositories (synchronize previously initialized git-annex repositories only)
- [X] Verify Git-annex repositories
- [X] Archive photos and videos to a date- and time based directory structure
- [ ] Re-encode audio
- [X] Re-encode (and merge) video
- [X] ~~Backup Git repositories~~ (not needed, archive directories instead)
- [X] ~~Backup Subversion repositories~~ (not needed, archive directories instead)

Backup configuration:

- [X] Actions
- [X] Logging
- [X] Includes and templates
- [X] Variable substitution

Backup operation:

- [X] Command line interface (CLI)
- [X] Store timestamps
- [X] Run outdated backups automatically
- [X] Warn for outdated backups
- [X] All-or-nothing transaction support for consistent multi-action backups
- [ ] Error handling
- [ ] Continuous logging (instead of buffering until the subprocesses finish)
- [ ] Colors for CLI
- [ ] Graphical user interface (GUI) (?)

Other stuff:

- [ ] Localization (en, nl...) (?)

## License

Better Safe Than Sorry is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License [along with this program](./COPYING.md). If not, see <https://www.gnu.org/licenses/>. 

## Contact

Maarten De Munck

Email: <maarten@vijfendertig.be> \
LinkedIn: <https://www.linkedin.com/in/maartendemunck/>
