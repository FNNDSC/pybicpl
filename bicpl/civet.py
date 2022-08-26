import shutil
import functools
from typing import Callable


def needs_civet(f: Callable):
    """A decorator which indicates the function depends on CIVET binaries."""
    @functools.wraps(f)
    def inner(*args, **kwargs):
        if not shutil.which('depth_potential'):
            raise CivetNotInstalledError()
        return f(*args, **kwargs)
    return inner


class CivetNotInstalledError(Exception):
    pass
