# Better Safe Than Sorry

Custom backups made easy.

Copyright (C) 2022-2026 Maarten De Munck (<maarten@vijfendertig.be>).

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
    description: full filesystem backup of Wormwood
    actions:
      - description: backup / filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-root.tar.bz2
        destination-compression: pbzip2 -9
        keep: 2
        retry: 3
        excludes:
          - ./sys
          - ./var/cache/apt/archives
          - ./var/lib/docker
          - ./var/lib/samba/private/msg.sock
          - ./var/log/journal
      - description: backup /boot filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /boot/
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-boot.tar.bz2
        destination-compression: pbzip2 -9
        keep: 2
      - description: backup /boot/efi filesystem
        action: ArchiveFiles
        all-or-nothing: true
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /boot/efi/
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-efi.tar.bz2
        destination-compression: pbzip2 -9
        keep: 2
  wormwood-maartenathome:
    description: maarten@home website data
    actions:
      - description: Archive maarten@home django database
        action: ArchivePostgreSQL
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: maartenathome-maartenathome-postgres-1
        source-database: maartenathome@maartenathome
        destination-file: /srv/backup/hosts/wormwood/data/maartenathome-database.sql.bz2
        destination-compression: pbzip2 -9
        keep: 3
      - description: Archive maarten@home django media (option 1)
        action: ArchiveFiles
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: django@maartenathome-maartenathome-django-1
        source-directory: /srv/django/media/
        destination-file: /srv/backup/hosts/wormwood/data/maartenathome-media.tar.bz2
        destination-compression: pbzip2 -9
        keep: 3
      - description: Synchronize maarten@home django media (option 2, part 1)
        action: RsyncFiles
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: django@maartenathome-maartenathome-django-1
        source-directory: /srv/django/media/
        destination-directory: /srv/backup/staging/hosts/wormwood/data/maartenathome-media/
        fake-super: true
      - description: Archive syncronized maarten@home django media (option 2, part 2)
        action: ArchiveFiles
        source-host: maarten@wormwood.home.vijfendertig.be
        source-directory: /srv/backup/staging/hosts/wormwood/data/maartenathome-media/
        destination-file: /srv/backup/hosts/wormwood/data/maartenathome-media-synchronized.tar.bz2
        destination-compression: pbzip2 -9
        keep: 3
loggers:
  - logger: File
    filename: /home/maarten/.local/log/bettersafethansorry.log
    append: true
```

The configuration file defines two backups:

- `wormwood-image` makes a full filesystem backup, split in one `.tar.bz2` archive for each filesystem (`/`, `/boot` and `/boot/efi`). I always run this backup from my desktop PC (rather than on wormwood itself), so no `destination-host` is needed: `source-host` fetches the (uncompressed) tar stream from wormwood over ssh, and since my desktop PC has a decent LAN connection and a much more performant CPU than the mini server, `destination-compression` bzip2s it locally on the desktop instead of taxing the mini server's CPU. The `all-or-nothing: true` flag ensures that all three filesystem backups are consistent: all backups are first prepared (creating temporary `.tmp` files), and only if all preparations succeed are the backups committed (rotating old backups and moving `.tmp` files to their final names). If any preparation fails, all temporary files are rolled back, ensuring you never have a mix of old and new backups from different points in time.
- `wormwood-maartenathome` makes a backup of the Django database in the maarten@home PostgreSQL container and the data directory in the maarten@home Django container. The backups are made to whatever system runs the backup (the data is important and the backup is not that big, so I sometimes just backup to my laptop if my desktop is off). Again, compression is done on the system running the backup. The example shows two approaches to make a snapshot of the Django media directory: option 1 makes a snapshot directly from the source Docker container, while option 2 first synchronizes the source to a local staging directory using `RsyncFiles` and then makes a snapshot of that local directory with a second `ArchiveFiles` action, decreasing network traffic significantly in case the data is mostly static. Both approaches use `source-container` to reach into the container via `docker exec` on `source-host` (so `rsync` must be installed inside the container image, and the `source-host` user must be allowed to run `docker exec`); the second, archiving action of option 2 no longer needs `source-container`, since by then the data is already available locally. The container's files are typically owned by container-internal uids/gids that don't correspond to real accounts on the system running the backup, so `fake-super: true` is set on the `RsyncFiles` step to preserve that ownership information in an extended attribute instead of failing to `chown`/`chgrp` it for real.

Logs are stored in a simple text file `~/.local/log/bettersafethansorry.log` and subsequent invocations just add their logs to the file.

`bsts list` lists the available backups. `bsts status` lists all backups and shows which backups are outdated.

`bsts do wormwood-image` and `bsts do wormwood-maartenathome` run the individual backups.

`bsts verify wormwood-image` and `bsts verify wormwood-maartenathome` verify the backups:

- Git-annex repositories: Checks for missing or corrupted files, checksum mismatches, and repository consistency using `git annex fsck`
- Archive backups (ArchiveFiles, ArchiveMySQL, ArchiveMariaDB, ArchivePostgreSQL): Verifies backup file exists and validates compression/archive integrity by decompressing and (for tar archives) listing contents

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
