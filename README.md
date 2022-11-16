# Better Safe Than Sorry

Custom backups made easy.

Copyright (C) 2022 Maarten De Munck (<maarten@vijfendertig.be>)

## About Better Safe Than Sorry

I have quite some Linux systems at home which contain various types of data ranging from normal files, git (and some old svn) repositories, databases to the git-annex repository which I use to store my full archive. Some of this data is quite important for me, so a reliable backup strategy is imperative.

I started with a simple shell script copying important files to external USB drives a long time ago (in 2014, according to my git history). Over time, I collected a large number of shell functions for all different types of data and a lot of code to call the right functions for every possible backup. And functions to verify backups of course, since a corrupted backup is even more frustrating than no backup at all.

To make things a bit easier to maintain, I started writing Better Safe Than Sorry. The main goal is to create a library of my backup functions, a system to configure all my backups and a way to run the backups, either manually (for backups from and to mobile devices) or automatic (from and to remote systems).

## Getting Started

## Usage

## Roadmap

Backup functions:

- [ ] Copy files and directories, both local and remote
- [ ] Archive files, directories and filesystems, both local and remote
- [ ] Archive photos and videos to a date- and time based directory structure
- [ ] Re-encode movies
- [ ] Backup PostgreSQL database
- [ ] Backup Git repositories
- [ ] Backup Subversion repositories
- [ ] Backup files and directories from a docker container
- [ ] Archive files, directories and filesystems from a docker container
- [ ] Backup PostgreSQL containers

Backup configuration:

- [ ] Actions
- [ ] Variable substitution
- [ ] Logging
- [ ] Action templates

Backup orchestrator:

- [ ] Manual invocation
- [ ] Store timestamps
- [ ] Automatic backups based on timestamps
- [ ] Warning for backups that are too old

## License

Better Safe than Sorry is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License [along with this program](./COPYING.md). If not, see <https://www.gnu.org/licenses/>. 

## Contact

Maarten De Munck

Email: <maarten@vijfendertig.be> \
LinkedIn: <https://www.linkedin.com/in/maartendemunck/>
