import datetime
import re
import requests
from bettersafethansorry.loggers import Logger


class ApiRegistrar(Logger):

    @staticmethod
    def _parse_seconds(value):
        if value in (None, "null"):
            return None
        return datetime.timedelta(seconds=float(value))

    def __init__(self, config, logger) -> None:
        try:
            # self.username = config['username']
            # self.password = config['password']
            self.info_url = config['info-url']
            self.update_url = config['update-url']
            self.api_token = config.get('api-token', None)
        except KeyError:
            logger.log_error('Error in API registrar config')
            raise ValueError('Error in API registrar config')
        self.backups = {}

    def start_backup(self, timestamp, id, name, description):
        self.backups[id] = name

    def finish_backup(self, timestamp, id, errors):
        name = self.backups.pop(id, None)
        if name is None or errors:
            return

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

        payload = {
            "type": "backup",
            "timestamp": timestamp.isoformat()
        }
        headers = {
            "X-Backup-Token": self.api_token} if hasattr(self, 'api_token') else {}
        response = requests.post(
            self.update_url.format(name=name),
            json=payload,
            headers=headers,
            timeout=10)
        response.raise_for_status()

    def is_backup_outdated(self, timestamp, name):
        headers = {
            "X-Backup-Token": self.api_token} if hasattr(self, 'api_token') else {}
        response = requests.get(
            self.info_url.format(name=name),
            headers=headers,
            timeout=10)
        if response.status_code != 200:
            return None

        info = response.json()
        backup = info.get("backup") or {}
        last_raw = backup.get("last")
        if not last_raw:
            return None
        last = datetime.datetime.fromisoformat(last_raw)

        interval = backup.get("interval") or {}
        preferred = interval.get("preferred")
        if not preferred:
            return None
        preferred_interval = ApiRegistrar._parse_seconds(preferred)
        if interval is None:
            return None

        return timestamp - last > preferred_interval
