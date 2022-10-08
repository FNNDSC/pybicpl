import os
import functools

import argparse
import numpy as np
from dataclasses import dataclass
from typing import Union, Iterable, TextIO

from bicpl import PolygonObj
from bicpl._version import __version__


@dataclass(frozen=True)
class WavefrontObj:
    """
    A representation of Wavefront OBJ file data.

    WARNING: Wavefront uses 1-indexing however Python lists start at 0.
    """
    vertices: list[tuple[float, float, float]]
    faces_raw: list[tuple[int, int, int]]
    index_offset: int = -1
    """
    Value added to a face coordinate to obtain its corresponding list index.
    """

    @classmethod
    def from_handle(cls, handle: Iterable[str]) -> 'WavefrontObj':
        """Parse a Wavefront OBJ file."""
        verts = []
        faces = []

        # remove comments from stream
        data = filter(None, map(cls._strip_comment, handle))

        for line in data:
            letter, *t = line.split()
            if not len(t) == 3:
                raise ValueError(f'Line is not 3D: "{line.strip()}"')
            if letter == 'v':
                verts.append(tuple(map(float, t)))
            elif letter == 'f':
                # wavefront is one-indexed
                faces.append(tuple(map(int, t)))
        return cls(verts, faces)  # type: ignore

    @staticmethod
    def _strip_comment(s: str):
        parts = s.split('#', 1)
        return parts[0].strip()

    @classmethod
    def from_file(cls, filename: Union[str, os.PathLike]) -> 'WavefrontObj':
        with open(filename) as f:
            return cls.from_handle(f)

    def to_mni(self) -> PolygonObj:
        """
        Convert to MNI format surface object.
        """
        mni_obj = PolygonObj.from_data(
            verts=np.array(self.vertices, dtype=np.float32),
            faces=np.array(self.faces_indices, dtype=np.uint32),
            normals=np.zeros((len(self.vertices), 3), dtype=np.float32)
        )
        return mni_obj.fix_normals()

    @classmethod
    def from_mni(cls, obj: PolygonObj) -> 'WavefrontObj':
        """
        Convert from MNI obj to Wavefront obj object.
        """
        vertices = obj.point_array
        faces = np.reshape([i + 1 for i in obj.indices], (len(obj.indices) // 3, 3))
        return cls(vertices, faces)

    # noinspection PyTypeChecker
    @functools.cached_property
    def faces_indices(self) -> list[tuple[int, int, int]]:
        return [tuple(i + self.index_offset for i in face) for face in self.faces_raw]

    def write_to(self, file: TextIO) -> None:
        file.write(f"Generated with {__package__} {__version__}\n")
        for vert in self.vertices:
            file.write(self._vec2txt('v', vert))
        for face in self.faces_raw:
            file.write(self._vec2txt('f', face))

    @staticmethod
    def _vec2txt(letter: str, v: Iterable) -> str:
        return f'{letter} {" ".join(map(str, v))}\n'

    def save(self, filename: Union[str, os.PathLike]) -> None:
        with open(filename, 'w') as f:
            self.write_to(f)

    def to_freesurfer_asc(self, filename: Union[str, os.PathLike]):
        with open(filename, 'w') as out:
            out.write(f'#!ascii\n')
            out.write(f'{len(self.vertices)} {len(self.faces_indices)}\n')
            for vert in self.vertices:
                out.write(f'{" ".join(map(str, vert))} 0\n')
            for face in self.faces_indices:
                out.write(f'{" ".join(map(str, face))} 0\n')


_parser = argparse.ArgumentParser()
_parser.add_argument('input_file', metavar='input.obj',
                     help='input file')
_parser.add_argument('output_file', metavar='output.obj',
                     help='output file')


def mni2wavefront():
    _parser.description = 'Convert MNI surface to Wavefront obj'
    options = _parser.parse_args()
    mni_obj = PolygonObj.from_file(options.input_file)
    wf_obj = WavefrontObj.from_mni(mni_obj)
    wf_obj.save(options.output_file)


def wavefront2mni():
    _parser.description = 'Convert Wavefront obj to MNI surface'
    options = _parser.parse_args()
    wf_obj = WavefrontObj.from_file(options.input_file)
    mni_obj = wf_obj.to_mni()
    mni_obj.save(options.output_file)


def wavefront2asc():
    _parser.description = 'Convert Wavefront obj to Freesurfer ascii surface'
    options = _parser.parse_args()
    wf_obj = WavefrontObj.from_file(options.input_file)
    wf_obj.to_freesurfer_asc(options.output_file)
