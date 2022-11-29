# Better Safe Than Sorry

Custom backups made easy.

Copyright (C) 2022 Maarten De Munck (<maarten@vijfendertig.be>)

## About Better Safe Than Sorry

I have quite some Linux systems at home which contain various types of data ranging from normal files, git (and some old svn) repositories, databases to the git-annex repository which I use to store my full archive. Some of this data is quite important for me, so a reliable backup strategy is imperative.

I started with a simple shell script copying important files to external USB drives a long time ago (in 2014, according to my git history). Over time, I collected a large number of shell functions for all different types of data and a lot of code to call the right functions for every possible backup. And functions to verify backups of course, since a corrupted backup is even more frustrating than no backup at all.

To make things a bit easier to maintain, I started writing Better Safe Than Sorry. The main goal is to create a library of my backup functions, a system to configure all my backups and a way to run the backups, either manually (for backups from and to mobile devices) or automatic (from and to remote systems).

## Installation

## Getting Started

To decrease my electricity consumption, I recently bought a mini server (wormwood) to run some applications that previously ran on my desktop PC (calvin) so that I can just shut down my desktop PC when I'm not using it. This system currently runs my maarten@home website with some webapps and a Gitea service and is the perfect example to show how Better Safe Than Sorry works.

The most important data on this system are of course the data (database and media files) of my maarten@home website and the data (database, repositories and media files) of the Gitea service. Now and then, I want to make a full system backup, but since both my maarten@home website and the Gitea service run from docker containers and their configuration is already stored in Git repositories, that's only needed to reduce the recovery time if the SSD fails. No data is lost if the full system backup is a bit outdated.

These requirements yield this configuration file `~/.config/bettersafethansorry.yaml` for Better Safe Than Sorry:

```yaml
backups:
  wormwood-image:
    description: Full filesystem backup of Wormwood
    actions:
      - description: Backup / filesystem
        action: ArchiveFiles
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /
        destination-host: maarten@calvin.home.vijfendertig.be
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-root.tar.bz2
        destination-compression: /usr/bin/bzip2 -9
        keep: 3
      - description: Backup /boot filesystem
        action: ArchiveFiles
        one-file-system: true
        source-host: root@wormwood.home.vijfendertig.be
        source-directory: /boot/
        destination-host: maarten@calvin.home.vijfendertig.be
        destination-file: /srv/backup/hosts/wormwood/images/wormwood-boot.tar.bz2
        destination-compression: /usr/bin/bzip2 -9
        keep: 3
      - description: Backup /boot/efi filesystem
        action: ArchiveFiles
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
  wormwood-gitea:
    description: Gitea@home
    actions:
      - description: Archive Gitea database
        action: ArchivePostgreSQL
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: maartenathome-gitea-postgres-1
        source-database: gitea@gitea
        destination-file: /srv/backup/hosts/wormwood/data/gitea-database.sql.bz2
        destination-compression: bzip2
        keep: 3
      - description: Archive Gitea configuration and repositories
        action: ArchiveFiles
        source-host: maarten@wormwood.home.vijfendertig.be
        source-container: maartenathome-gitea-server-1
        source-directory: /data/
        minimalistic-tar: true
        destination-file: /srv/backup/hosts/wormwood/data/gitea-data.tar.bz2
        destination-compression: bzip2
        keep: 3
loggers:
  - logger: File
    filename: /home/maarten/.local/log/bettersafethansorry.log
    append: true
```

The configuration file defines three backups:

- `wormwood-image` makes a full filesystem backup, split in one `.tar.bz2` archive for each filesystem (`/`, `/boot` and `/boot/efi`). The backups are made to my desktop PC and because I have a decent LAN at home and the CPU of my desktop PC is much more performant than the CPU of the mini server, I bzip2 the tar archives on the desktop PC.
- `wormwood-maartenathome` makes a backup of the Django database in the maarten@home PostgreSQL container and the data directory in the maarten@home Django container. The backups are made to whatever system runs the backup (the data is important and the backup is not that big, so I sometimes just backup to my laptop if my desktop is off). Again, compression is done on the system running the backup.
- `wormwood-gitea` makes a backup of the Gitea database in the Gitea PostgreSQL container and the data directory in the Gitea server container. Again, backups are made to whatever system runs the backup and compression is done on the system running the backup.

Logs are stored in a simple text file `~/.local/log/bettersafethansorry.log` and subsequent invocations just add their logs to the file.

`bsts list` lists the available backups and `bsts do wormwood-image`, `bsts do wormwood-maartenathome` and `bsts do wormwood-gitea` run the individual backups.

## Usage

### Command Line Interface

Usage: `bsts [-h] [-c CONFIG] [-n] command [backup]`

Positional arguments:

- `command`: `list` or `do`
- `backup`: backup to perform (as defined in the configuration file)

Options:

- `-h` or `--help`: show this help message and exit
- `-c CONFIG` or `--config CONFIG`: select configuration file
- `-n` or `--dry-run`: do not actually perform actions, only log them

### Configuration file

## Roadmap

Backup functions:

- [X] Rsync files and directories, both local and remote
- [X] Archive files, directories and filesystems, both local and remote, both native and in a docker container
- [X] Backup PostgreSQL databases, both local and remote, both native and in a docker container
- [X] Backup Git-annex repositories (synchronize previously initialized git-annex repositories only)
- [ ] Archive photos and videos to a date- and time based directory structure
- [ ] Re-encode movies
- [ ] Backup Git repositories
- [ ] Backup Subversion repositories
- [ ] Verify backups

Backup configuration:

- [X] Actions
- [X] Logging
- [ ] Templates
- [ ] Variable substitution

Backup operation:

- [X] Command line interface (CLI)
- [ ] Store timestamps
- [ ] Run outdated backups automatically
- [ ] Warn for outdated backups
- [ ] Continuous logging (instead of buffering until the subprocesses finish)
- [ ] Graphical user interface (GUI)

Other stuff:

- [ ] Localization (en, nl...)

## License

Better Safe Than Sorry is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License [along with this program](./COPYING.md). If not, see <https://www.gnu.org/licenses/>. 

## Contact

Maarten De Munck

Email: <maarten@vijfendertig.be> \
LinkedIn: <https://www.linkedin.com/in/maartendemunck/>
