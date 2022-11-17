import argparse


def run():
    parser = argparse.ArgumentParser(
        description='Better Safe Than Sorry. Custom backups made easy.')
    parser.add_argument(
        'command', help='Select backup (set of actions) to perform')
    parser.add_argument('-c', '--config', help='Select configuration file')
    parser.add_argument('-n', '--dry-run',
                        help='Only display actions', action='store_true')
    args = parser.parse_args()
    print('Command      : {}'.format(args.command))
    print('Configuration: {}'.format(args.config))
    print('Dry run      : {}'.format(args.dry_run))


if __name__ == '__main__':
    run()
