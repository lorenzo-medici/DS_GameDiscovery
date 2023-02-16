from Broker.rwlock import ReadWriteLock, WriteRWLock, ReadRWLock


class Registry:

    # TODO: Add logging
    # TODO: Add timer for removing stale entries

    def __init__(self):
        self._registry = {}  # Map<String, (String, Bool)>

        self._lock = ReadWriteLock(withPromotion=True)
        self._readLock = ReadRWLock(self._lock)
        self._writeLock = WriteRWLock(self._lock)

        # string lock is not needed in python since strings are immutable and assignment is atomic
        self._to_string = ''
        self._generate_string()

    def remove_old(self):
        with self._writeLock:
            for name in self._registry.keys():
                t = self._registry.get(name)
                if not t[1]:  # stale entry
                    self._registry.pop(name)
                else:
                    self._registry.update({name: (t[0], False)})  # reset entry

        self._generate_string()

    def add_server(self, name, addr):
        self._lock.acquire_read()
        if name in self._registry.keys():
            if self._registry.get(name)[0] == addr:  # renew
                self._lock.release_read()
                with self._writeLock:
                    self._registry.update({name: (addr, True)})
                result = "renewed"
            else:  # taken
                self._lock.release_read()
                result = "taken"
        else:  # add
            self._lock.release_read()
            with self._writeLock:
                self._registry.update({name: (addr, True)})
            self._generate_string()
            result = "okay"

        return result

    def _generate_string(self):
        with self._readLock:
            listOfEntries = [f'{name}|{self._registry.get(name)[0]}' for name in self._registry.keys()]
            self._to_string = '$'.join(listOfEntries)

    def get_string(self):
        return self._to_string
