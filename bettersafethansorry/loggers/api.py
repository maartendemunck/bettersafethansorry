import requests


class ApiRegistrar:

    def __init__(self, config, logger) -> None:
        try:
            # self.username = config['username']
            # self.password = config['password']
            self.info_url = config['info-url']
            self.update_url = config['update-url']
        except KeyError:
            logger.log_error('Error in API registrar config')
            raise ValueError('Error in API registrar config')
        self.backups = {}

    def start_backup(self, timestamp, id, name, description):
        self.backups[id] = name

    def finish_backup(self, timestamp, id, errors):
        name = self.backups.pop(id, None)
        if name is not None and len(errors) == 0:
            request = {'type': 'backup',
                       'timestamp': timestamp.isoformat()}
            requests.post(self.update_url.format(name=name), json=request)

    def start_action(self, timestamp, id, description):
        pass

    def finish_action(self, timestamp, id, errors):
        pass

    def log_message(self, timestamp, level, message):
        pass
