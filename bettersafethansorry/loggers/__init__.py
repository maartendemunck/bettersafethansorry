class Logger:

    def __init__(self):
        pass

    def start_backup(self, timestamp, id, name, description):
        pass

    def finish_backup(self, timestamp, id, errors):
        pass

    def start_action(self, timestamp, id, description):
        pass

    def finish_action(self, timestamp, id, errors):
        pass

    def log_message(self, timestamp, level, message):
        pass

    def is_backup_outdated(self, timestamp, name):
        return None

    def start_verify(self, timestamp, id, name, description):
        pass

    def finish_verify(self, timestamp, id, errors):
        pass
