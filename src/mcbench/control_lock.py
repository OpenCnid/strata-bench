"""Operator-store profile operation locks; complements the native profile writer lock."""

import os
from contextlib import contextmanager
from functools import partial

from .storage import Fault, digest, reject_links


@contextmanager
def profile_operation(database, profile_id):
    directory = database.path.parent / (database.path.name + ".control-locks")
    reject_links(directory)
    directory.mkdir(exist_ok=True)
    path = directory / (digest(profile_id) + ".lock")
    reject_links(path)
    with path.open("a+b") as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            lock = partial(msvcrt.locking, stream.fileno(), msvcrt.LK_NBLCK, 1)
            unlock = partial(msvcrt.locking, stream.fileno(), msvcrt.LK_UNLCK, 1)
        elif os.name == "posix":
            import fcntl
            lock = partial(fcntl.flock, stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            unlock = partial(fcntl.flock, stream.fileno(), fcntl.LOCK_UN)
        else:
            raise Fault("SETTINGS_LOCK_UNSUPPORTED")
        try:
            lock()
        except OSError:
            raise Fault("SETTINGS_BUSY") from None
        try:
            yield
        finally:
            stream.seek(0)
            unlock()
