import datetime
import re
import requests
from bettersafethansorry.loggers import Logger


class ApiRegistrar(Logger):

    iso8601_duration_re = re.compile(
        r'^(?P<sign>[-+]?)'
        r'P'
        r'(?:(?P<days>\d+(.\d+)?)D)?'
        r'(?:T'
        r'(?:(?P<hours>\d+(.\d+)?)H)?'
        r'(?:(?P<minutes>\d+(.\d+)?)M)?'
        r'(?:(?P<seconds>\d+(.\d+)?)S)?'
        r')?'
        r'$'
    )

    @staticmethod
    def __parse_duration(value):
        match = (
            ApiRegistrar.iso8601_duration_re.match(value)
        )
        if match:
            kw = match.groupdict()
            days = datetime.timedelta(float(kw.pop('days', 0) or 0))
            sign = -1 if kw.pop('sign', '+') == '-' else 1
            if kw.get('microseconds'):
                kw['microseconds'] = kw['microseconds'].ljust(6, '0')
            if kw.get('seconds') and kw.get('microseconds') and kw['seconds'].startswith('-'):
                kw['microseconds'] = '-' + kw['microseconds']
            kw = {k: float(v) for k, v in kw.items() if v is not None}
            return days + sign * datetime.timedelta(**kw)

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

    def is_outdated(self, timestamp, name):
        response = requests.get(self.info_url.format(name=name))
        if response.status_code != 200:
            return None
        try:
            info = response.json()
            last = datetime.datetime.fromisoformat(
                info['backup']['last'].replace('Z', '+00:00'))
            interval = ApiRegistrar.__parse_duration(
                info['backup']['interval']['preferred'])
            return (timestamp - last > interval)
        except:
            return None
