import logging
from threading import Timer

from rwlock import ReadWriteLock, WriteRWLock, ReadRWLock

N_MINUTES = 5


class Registry:

    def __init__(self, logger):
        self._registry = {}  # Map<String, (String, Bool)>

        self._lock = ReadWriteLock(withPromotion=True)
        self._readLock = ReadRWLock(self._lock)
        self._writeLock = WriteRWLock(self._lock)

        # string lock is not needed in python since strings are immutable and assignment is atomic
        self._to_string = ''
        self._generate_string()

        self._logger = logger

        self._timer = RepeatTimer(N_MINUTES * 60, self.remove_old)
        self._timer.start()

    def stop_timer(self):
        self._timer.cancel()

    def remove_old(self):
        with self._writeLock:
            for name in list(self._registry.keys()):
                t = self._registry.get(name)
                if not t[1]:  # stale entry
                    self._registry.pop(name)
                    self._logger.log(level=logging.DEBUG, msg=f'Stale server {name} removed')
                else:
                    self._registry.update({name: (t[0], False)})  # reset entry
                    self._logger.log(level=logging.DEBUG, msg=f'Non-stale server {name} kept')

        self._generate_string()

    def add_server(self, name, addr):
        self._lock.acquire_read()
        if name in self._registry.keys():
            if self._registry.get(name)[0] == addr:  # renew
                self._lock.release_read()
                with self._writeLock:
                    self._registry.update({name: (addr, True)})
                result = "renewed"
                self._logger.log(level=logging.INFO, msg=f"Server {name} renewed")
            else:  # taken
                self._lock.release_read()
                result = "taken"
                self._logger.log(level=logging.WARNING,
                                 msg=f"Server {name} already taken with address different from {addr}")
        else:  # add
            self._lock.release_read()
            with self._writeLock:
                self._registry.update({name: (addr, True)})
            self._generate_string()
            result = "okay"
            self._logger.log(level=logging.INFO, msg=f'Server {name} added')

        return result

    def _generate_string(self):
        with self._readLock:
            listOfEntries = [f'{name}|{self._registry.get(name)[0]}' for name in self._registry.keys()]
            self._to_string = '$'.join(listOfEntries)

    def get_string(self):
        return self._to_string


# Perpetual timer with set delay
# SOURCE: https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
