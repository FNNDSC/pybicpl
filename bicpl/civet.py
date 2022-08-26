import functools
import shutil
import subprocess as sp
from tempfile import NamedTemporaryFile
from typing import Callable, TypeVar, Union

import numpy as np
import numpy.typing as npt

_T = TypeVar('_T', bound=Union[np.float32, np.float64])


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


@needs_civet
def depth_potential(filename, arg='', command='depth_potential', dtype: _T = np.float32) -> npt.NDArray[_T]:
    """
    :param filename: input.obj
    :param arg: See "depth_potential -help" for options.
    :param command: Specify path to the depth_potential binary
    :param dtype: numpy array dtype
    :return: the result of depth_potential as a numpy array in memory.
    """
    if not arg.startswith('-'):
        arg = '-' + arg
    with NamedTemporaryFile() as tmp:
        sp.run([command, arg, filename, tmp.name])
        data = np.loadtxt(tmp.name, dtype=dtype)
    return data
