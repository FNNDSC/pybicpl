import os

import numpy as np
import numpy.typing as npt
from dataclasses import dataclass
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
    is assigned to each polygon. The length of this array must be equal to the
    greatest value in the `end_indices` array plus one.
    """

    def __post_init__(self):
        if self.colour_flag != 0:
            raise ValueError('colour_flag must be 0')

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

    def save(self, filename: str | os.PathLike):
        """
        Write this object to a file.
        """
        with open(filename, 'w') as out:
            header = ['P', self.surfprop.A, self.surfprop.D,
                      self.surfprop.S, self.surfprop.SE,
                      self.surfprop.T, self.n_points]
            out.write(_list2str(header) + '\n')

            for point in self.point_array:
                out.write(' ' + _list2str(point) + '\n')

            for vector in self.normals:
                out.write(' ' + _list2str(vector) + '\n')

            out.write(f'\n {self.nitems}\n')
            out.write(f' {self.colour_flag} {self.colour_table}\n\n')

            for i in range(0, self.nitems, 8):
                out.write(' ' + _list2str(self.end_indices[i:i + 8]) + '\n')

            for i in range(0, len(self.indices), 8):
                out.write(' ' + _list2str(self.indices[i:i + 8]) + '\n')

    @classmethod
    def from_file(cls, filename: str | os.PathLike) -> 'PolygonObj':
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
        points_array = [np.float32(x) for x in data[start:end]]
        points_array = np.reshape(points_array, (n_points, 3,))

        start = end
        end = n_points * 3 + start
        normals = [np.float32(x) for x in data[start:end]]
        normals = np.reshape(normals, (n_points, 3,))

        nitems = int(data[end])

        colour_flag = int(data[end+1])
        if colour_flag != 0:
            print(f'nitems is {nitems}, colour_flag is {colour_flag}')
            raise ValueError('colour_flag is not 0')
        start = end + 2
        end = start + 4
        colour_table = tuple(np.float32(x) for x in data[start:end])

        start = end
        end = start + nitems
        end_indices = tuple(int(i) for i in data[start:end])

        start = end
        end = start + end_indices[-1] + 1
        indices = tuple(int(i) for i in data[start:end])

        return cls(
            surfprop=surfprop,
            n_points=n_points,
            point_array=points_array,
            normals=normals,
            nitems=nitems,
            colour_flag=colour_flag,
            colour_table=colour_table,
            end_indices=end_indices,
            indices=indices
        )


def _list2str(array):
    """
    Join a list with spaces between elements.
    """
    return ' '.join(str(a) for a in array)
