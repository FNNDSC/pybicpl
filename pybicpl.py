# -*- coding: utf-8 -*-
"""
2019-08-21

Parser for the MNI .obj file format
http://www.bic.mni.mcgill.ca/users/mishkin/mni_obj_format.pdf

While I would have loved to try programming in C and bicpl,
I couldn't figure out the DepEndeNCiEs.

@author: Jennings Zhang <jenni_zh@protonmail.com>
"""

import numpy as np
from tempfile import NamedTemporaryFile
import subprocess as sp
from os import unlink


def write_file(filename, data):
    """
    Writes an iterable to a file.
    """
    with open(filename, 'w') as out:
        for value in data:
            out.write(str(value) + '\n')


def list2str(array):
    """
    Join a list with spaces between elements.
    """
    return ' '.join(str(a) for a in array)


def depth_potential(filename, arg='', command='depth_potential'):
    """
    :param filename: input.obj
    :param arg: See "depth_potential -help" for options.
    :param command: Specify path to the depth_potential binary
    :return: the result of depth_potential as a numpy array in memory.
    """
    if not arg.startswith('-'):
        arg = '-' + arg
    with NamedTemporaryFile() as tmp:
        sp.run([command, arg, filename, tmp.name])
        data = np.loadtxt(tmp.name, dtype=np.float32)
    return data


def local_da(neighbors, data, point_index):
    """
    Average absolute difference between the
    value at point_index and its neighbors.
    """
    return np.mean(np.abs(data[point_index] - data[list(neighbors)]))


def difference_average(neighbor_graph, data):
    """
    :return: lazy generator
    """
    return (local_da(n, data, i) for i, n in enumerate(neighbor_graph))


class MniObj:
    """
    Attributes:
        surfprop (dictionary): properties idk
        n_points (int): number of points
        points: matrix of points
        normals: matrix of normal vectors
        n_items (int): number of polygons
        end_indices (list): index values of separate polygons
        indices (list): connectivity
    """
    def __init__(self, filename=None):
        """
        Parses a .obj file.
        If filename is not provided, then a unit sphere is created.
        """
        self.filename = filename
        if filename:
            with open(filename, 'r') as f:
                data = f.readlines()
        else:
            with NamedTemporaryFile(suffix="_81920.obj") as tmp:
                command = ['create_tetra', tmp.name,
                       '0', '0', '0', '1', '1', '1', '81920']
                sp.run(command, stdout=sp.DEVNULL, check=True)
                with open(tmp.name, 'r') as f:
                    data = f.readlines()
        data = ''.join(data).split()

        # file whitespace is not strictly enforced
        if data[0] != 'P':
            raise ValueError('Only Polygons supported, ' + filename)

        sp = tuple(float(value) for value in data[1:6])
        self.surfprop = {
                'A': sp[0], 'D': sp[1], 'S': sp[2],
                'SE': int(sp[3]), 'T': int(sp[4])
        }

        self.n_points = int(data[6])

        start = 7
        end = self.n_points * 3 + start
        self.points = [np.float32(value) for value in data[start:end]]
        self.points = np.reshape(self.points, (self.n_points, 3,))

        start = end
        end = self.n_points * 3 + start
        self.normals = [np.float32(value) for value in data[start:end]]
        self.normals = np.reshape(self.normals, (self.n_points, 3,))

        self.n_items = int(data[end])

        # TODO color support
        if data[end+1] != '0':
            raise ValueError('colour_flag is not 0 in ' + filename)
        start = end + 2
        end = start + 4
        self.colour = [np.float32(value) for value in data[start:end]]

        start = end
        end = start + self.n_items
        self.end_indices = [int(i) for i in data[start:end]]

        start = end
        end = start + self.end_indices[-1] + 1
        self.indices = [int(i) for i in data[start:end]]

    def neighbor_graph(self, triangles_only=True):
        """
        each neighborhood contains a vertex's neighbors
        (surrounding vertecies that are immediately connected to it)
        """
        prev = 0
        # create new set objects in memory for each point
        neighbors = [set() for x in self.points]
        for i in self.end_indices:
            shape = self.indices[prev:i]
            if triangles_only and len(shape) != 3:
                raise AssertionError('Found shape that is not a triangle in '
                                     + self.filename)
            for vertex in shape:
                for neighbor in shape:
                    if neighbor != vertex:
                        neighbors[vertex].add(neighbor)
            prev = i
        return neighbors

    def recompute_normals(self):
        """
        Uses depth_potential to calculate normal vectors.
        You should call this function after mutating the points matrix.
        """
        tmp = NamedTemporaryFile('w', suffix='_81920.obj', delete=False)
        self._write_to(tmp)
        tmp.close()
        self.normals = depth_potential(tmp.name, '-normals')
        unlink(tmp.name)

    def _write_to(self, out):
        header = ['P', self.surfprop['A'], self.surfprop['D'],
                  self.surfprop['S'], self.surfprop['SE'],
                  self.surfprop['T'], self.n_points]
        out.write(list2str(header) + '\n')

        for point in self.points:
            out.write(' ' + list2str(point) + '\n')

        for vector in self.normals:
            out.write(' ' + list2str(vector) + '\n')

        out.write('\n {}\n'.format(self.n_items))
        out.write(' 0 ' + list2str(self.colour) + '\n\n')

        for i in range(0, self.n_items, 8):
            out.write(' ' + list2str(self.end_indices[i:i+8]) + '\n')

        for i in range(0, len(self.indices), 8):
            out.write(' ' + list2str(self.indices[i:i+8]) + '\n')

    def save(self, filename):
        with open(filename, 'w') as out:
            self._write_to(out)
