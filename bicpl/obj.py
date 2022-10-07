import dataclasses
import os
import subprocess as sp
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import TextIO, ContextManager, Union

import numpy as np
import numpy.typing as npt

from bicpl.civet import needs_civet, depth_potential
from bicpl.types import SurfProp, Colour


@dataclass(frozen=True)
class PolygonObj:
    """
    Polygonal mesh in `.obj` file format.

    http://www.bic.mni.mcgill.ca/users/mishkin/mni_obj_format.pdf

    Note: the data representation is neither efficient nor easy to work with.
    `PolygonObj` directly corresponds to the file format spec. It might be
    easier to work with proxy objects or just matrices instead.
    """
    surfprop: SurfProp
    """
    Surface properties for the polygons.
    """
    n_points: int
    """
    Number of distinct vertices in the aggregate polygon object.
    """
    point_array: npt.NDArray[np.float32]
    """
    List of distinct vertices that define this group of polygons. Note that vertices may
    be reused if the end indices and indices fields are set appropriately.
    """
    normals: npt.NDArray[np.float32]
    """
    List of point normals for each point.
    """
    nitems: int
    """
    Number of polygons defined.
    """
    colour_flag: int
    """
    A flag indicating the number of colours allocated in this object. A value of
    zero specifies that single colour applies to all line segments. A value of one
    specifies that colours are specified on a per-item basis. A value of two specifies
    that colours are specified on a per-vertex basis.
    """
    colour_table: tuple[Colour, ...]
    """
    The RGB colour values to be associated with the polygons. The length of this
    section may be either 1 (if `colour_flag` is 0), `nitems` (if `colour_flag` is 1) or
    `npoints` (if `colour_flag` is 2).
    """
    end_indices: tuple[int, ...]
    """
    This is a list of length nitems that specifies the index of the element in the indices
    list associated with each successive polygon.
    """
    indices: tuple[int, ...]
    """
    A list of integer indices into the `point_array` that specifies how each of the vertices
    is assigned to each polygon.
    """

    def __post_init__(self):
        if self.colour_flag != 0:
            raise ValueError('colour_flag must be 0')
        if self.nitems != len(self.end_indices):
            raise ValueError(f'{self.nitems} != {len(self.end_indices)}')
        if len(self.indices) != max(self.end_indices):
            # The spec says:
            # > The length of [indices] must be equal to the
            # > greatest value in the `end_indices` array plus one.
            # But it doesn't seem correct, since elements of `end_indices`
            # represent an exclusive index number, not an inclusive one.
            raise ValueError(f'{len(self.indices)} != {max(self.end_indices)}')

    def neighbor_graph(self, triangles_only=True) -> tuple[set[int], ...]:
        """
        Produces a tuple of the same length as `point_array` with values being
        sets of indices into `point_array` that are immediate neighbors with
        the corresponding vertex.
        """
        # maybe move this to a proxy object?
        prev = 0
        neighbors = tuple(set() for _ in self.point_array)
        for i in self.end_indices:
            shape = self.indices[prev:i]
            if triangles_only and len(shape) != 3:
                raise ValueError('Found shape that is not a triangle')
            for vertex in shape:
                for neighbor in shape:
                    if neighbor != vertex:
                        neighbors[vertex].add(neighbor)
            prev = i
        return neighbors

    def save(self, filename: Union[str, os.PathLike]):
        """
        Write this object to a file.
        """
        with open(filename, 'w') as out:
            self.write_to(out)

    def write_to(self, file: TextIO):
        header = ['P', self.surfprop.A, self.surfprop.D,
                  self.surfprop.S, self.surfprop.SE,
                  self.surfprop.T, self.n_points]
        file.write(_list2str(header) + '\n')

        for point in self.point_array:
            file.write(' ' + _list2str(point) + '\n')

        for vector in self.normals:
            file.write(' ' + _list2str(vector) + '\n')

        file.write(f'\n {self.nitems}\n')
        file.write(f' {self.colour_flag} {_serialize_colour_table(self.colour_table)}\n\n')

        for i in range(0, self.nitems, 8):
            file.write(' ' + _list2str(self.end_indices[i:i + 8]) + '\n')

        for i in range(0, len(self.indices), 8):
            file.write(' ' + _list2str(self.indices[i:i + 8]) + '\n')

    @classmethod
    def from_file(cls, filename: Union[str, os.PathLike]) -> 'PolygonObj':
        """
        Parse an `.obj` file.
        """
        with open(filename, 'r') as f:
            data = f.readlines()
        return cls.from_str('\n'.join(data))

    @classmethod
    def from_str(cls, s: str) -> 'PolygonObj':
        """
        Parse `.obj` data.
        """
        data = s.split()
        if data[0] != 'P':
            raise ValueError('Only Polygons supported')

        sp = tuple(float(value) for value in data[1:6])
        surfprop = SurfProp(A=sp[0], D=sp[1], S=sp[2], SE=int(sp[3]), T=int(sp[4]))

        n_points = int(data[6])

        start = 7
        end = n_points * 3 + start
        point_array = [np.float32(x) for x in data[start:end]]
        point_array = np.reshape(point_array, (n_points, 3,))

        start = end
        end = n_points * 3 + start
        normals = [np.float32(x) for x in data[start:end]]
        normals = np.reshape(normals, (n_points, 3,))

        nitems = int(data[end])

        colour_flag = int(data[end + 1])
        if colour_flag != 0:
            raise ValueError('colour_flag is not 0')
        start = end + 2
        end = start + 4
        colour_table = (Colour(tuple(np.float32(x) for x in data[start:end])),)

        start = end
        end = start + nitems
        end_indices = tuple(int(i) for i in data[start:end])

        start = end
        end = start + end_indices[-1] + 1
        indices = tuple(int(i) for i in data[start:end])

        return cls(
            surfprop=surfprop,
            n_points=n_points,
            point_array=point_array,
            normals=normals,
            nitems=nitems,
            colour_flag=colour_flag,
            colour_table=colour_table,
            end_indices=end_indices,
            indices=indices
        )

    @classmethod
    def from_data(cls, verts: npt.NDArray[np.float32], faces: npt.NDArray[np.uint32], normals: npt.NDArray[np.float32],
                  surfprop: SurfProp = SurfProp(A=0.3, D=0.3, S=0.4, SE=10, T=1),
                  colour_flag=0, colour_table=(Colour((1, 1, 1, 1)),)):
        """
        Create a `.obj` from raw data.

        Paremeters
        ----------
        verts: (V, 3) array
            Spatial coordinates for V unique mesh vertices.
        faces: (F, 3) array
            Define triangular faces via referencing vertex indices from `verts`.
        normals: (V, 3) array
            The normal direction at each vertex.
        """
        n_points = len(verts)
        nitems = len(faces)

        return cls(
            surfprop=surfprop,
            n_points=n_points,
            point_array=verts,
            normals=normals,
            nitems=nitems,
            colour_flag=colour_flag,
            colour_table=colour_table,
            end_indices=tuple(range(3, (nitems + 1) * 3, 3)),
            indices=tuple(faces.flatten())
        )

    @classmethod
    @needs_civet
    def from_tetra(cls,
                   origin: tuple[float, float, float] = (0, 0, 0),
                   radius: tuple[float, float, float] = (1, 1, 1),
                   n_triangles: int = 81920) -> 'PolygonObj':
        params = map(str, origin + radius + (n_triangles,))
        with NamedTemporaryFile(suffix='_81920.obj') as tmp:
            command = ['create_tetra', tmp.name, *params]
            sp.run(command, stdout=sp.DEVNULL, check=True)
            with open(tmp.name, 'r') as f:
                data = f.readlines()
        return cls.from_str('\n'.join(data))

    @needs_civet
    def reset_points(self, point_array: npt.NDArray[np.float32]) -> 'PolygonObj':
        """
        Create a new ``PolygonObj`` from this one, with a different ``point_array``,
        then recompute normal vectors by calling ``recompute_normals``.
        """
        updated = dataclasses.replace(self, point_array=point_array)
        return updated.fix_normals()

    def fix_normals(self) -> 'PolygonObj':
        """
        Use ``depth_potential`` to recompute this surface's normal vectors.

        Useful in situations where ``point_array`` was produced by a non-CIVET program.
        """
        return dataclasses.replace(self, normals=self.depth_potential(arg='-normals'))

    def depth_potential(self, arg: str) -> npt.NDArray[np.float32]:
        """
        Run depth_potential on this data, returning the result as a numpy array.
        """
        with self.as_file() as tmp:
            return depth_potential(tmp, arg)

    @contextmanager
    def as_file(self) -> ContextManager[str]:
        """
        Write this surface to a temporary file so that you can call subprocesses on it.
        """
        with NamedTemporaryFile('w', suffix='_81920.obj', delete=False) as tmp:
            self.write_to(tmp)
        yield tmp.name
        os.unlink(tmp.name)


def _list2str(array):
    """
    Join a list with spaces between elements.
    """
    return ' '.join(str(a) for a in array)


def _serialize_colour_table(ct: tuple[Colour, ...]) -> str:
    return ' '.join((' '.join(val for val in map(str, colour))) for colour in ct)
