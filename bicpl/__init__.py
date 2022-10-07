"""
Library for reading and writing MNI `.obj` surface files.
"""

from bicpl.obj import PolygonObj
from bicpl.wavefront import WavefrontObj
from bicpl._version import __version__

__docformat__ = 'numpy'

__all__ = [
    'PolygonObj',
    'WavefrontObj',
    'types',
    'math',
    '__version__'
]
