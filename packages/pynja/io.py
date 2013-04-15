import os


def create_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


def create_dir_for_file(f):
    d = os.path.dirname(f)
    create_dir(d)


def write_file_if_different(filePath, newContents):
    needToWrite = True
    if os.path.exists(filePath):
        with open(filePath, "rt") as file:
            oldContents = file.read()
            needToWrite = (oldContents != newContents)
    if needToWrite:
        create_dir_for_file(filePath)
        with open(filePath, "wt") as file:
            file.write(newContents)


class CrudeLockFile:
    def __init__(self, lockPath):
        self._lockPath = lockPath
        try:
            fd = os.open(lockPath, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            print("Failed to open lock file due to possible concurrent build.")
            print("If the lock file is stale, delete it and retry.")
            print("lockfile: " + lockPath)
            raise
        self._file = os.fdopen(fd)

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        self._file.close()
        os.unlink(self._lockPath)


if os.name == 'nt':
    def is_64bit_os():
        if os.getenv("PROCESSOR_ARCHITECTURE").upper() == "AMD64":
            return True
        if os.getenv("PROCESSOR_ARCHITEW6432").upper() == "AMD64":
            return True
        return False
