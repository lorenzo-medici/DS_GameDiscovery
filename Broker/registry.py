"""
Module containing the Registry class, and the accessory RepeatTimer class for removing stale entries
"""
import logging
from threading import Timer

from rwlock import ReadWriteLock, WriteRWLock, ReadRWLock

N_MINUTES = 5


class Registry:
    """
    This class implements a registry, where server can be registered based on their name and address.
    Internally it maps a name (string) to a pair of string and bool, representing the concatenation of
        address and port interlaved by a '|', and if the server has been renewed since the last removal
        of stale entries.
    Consistency is guaranteed by an instance of a ReadWriteLock, which allows parallel reads and locking
        writes.
    Removal of stale entries is performed by the RepeatTimer, that calls self.remove_old every N_MINUTES
        minutes. This function removes entries that have not been renewed since the last cleanup.
    """

    def __init__(self, logger):
        """
        Initializes the instance of the registry with all required components, logger, ReadWriteLock
            and RepeatTimer.
        :param logger: the logger object to use in this class
        """
        self._registry = {}  # Map<String, (String, Bool)>

        self._lock = ReadWriteLock(withPromotion=True)
        self._readLock = ReadRWLock(self._lock)
        self._writeLock = WriteRWLock(self._lock)

        # string lock is not needed in python since strings are immutable and assignment is atomic
        self._to_string = ''
        self._generate_string()

        self._logger = logger

        self._timer = RepeatTimer(90, self.remove_old)
        self._timer.start()

    def stop_timer(self):
        """
        Stops the RepeatTimer, used for teardown of the class
        """
        self._timer.cancel()

    def remove_old(self):
        """
        Removes stale entries. For each entry in the registry, the boolean value is checked.
        If it is True, the entry is not deleted and the attribute is set to False.
        If it is False, the entry is stale and is deleted.
        This operation requires a write lock for the entirety of its execution.
        """
        with self._writeLock:
            for name in list(self._registry.keys()):
                t = self._registry.get(name)
                if not t[1]:  # stale entry
                    self._registry.pop(name)
                    self._logger.log(level=logging.DEBUG, msg=f'Stale server {name} removed')
                else:  # reset entry
                    self._registry.update({name: (t[0], False)})
                    self._logger.log(level=logging.DEBUG, msg=f'Non-stale server {name} kept')

        self._generate_string()

    def add_server(self, name, addr):
        """
        This function tries to add a server to the registry. Some combination of read and write lock
            is needed for the different situations.
        :param name: A string representing the name the server, also used as the key in the dictionary
        :param addr: A string representing the address and port of the server concatenated with a '|'
            character
        :return: A string representing the result of the operation:
            'okay' if the server was added successfully
            'renewed' if the server was already registered (its attribute has been manually set to True)
            'taken' if a server with the same name but different address already exists
        """
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
        """
        Generates the string representation that will be returned to the client.
        """
        with self._readLock:
            listOfEntries = [f'{name}|{self._registry.get(name)[0]}' for name in self._registry.keys()]
            self._to_string = '$'.join(listOfEntries)

    def get_string(self):
        """
        :return: the string representation to transmit to the client
        """
        return self._to_string


# Perpetual timer with set delay
# SOURCE: https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    """
    When instantiated (and run) this class repeats the function contained in self.function every
        self.interval seconds.
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
