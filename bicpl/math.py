"""
Helper functions for computing metrics about surfaces.

https://ipfs.babymri.org/ipfs/QmZuoBXCwGB9Jqvoait1kTw75ogNoPcMnYFT6v1wAomco6/2019_fnndsc_subplate_surfaces.pdf
"""

from typing import Iterator
import numpy as np
import numpy.typing as npt


def _local_da(neighbors, data, point_index) -> np.float64:
    """
    Average absolute difference between the
    value at point_index and its neighbors.
    """
    return np.mean(np.abs(data[point_index] - data[list(neighbors)]))  # type: ignore


def difference_average(neighbor_graph: tuple[set[int], ...],
                       data: npt.NDArray[np.floating]
                       ) -> Iterator[np.float64]:
    """
    Average absolute difference between the
    value at point_index and its neighbors
    for every vertex in the given array.

    Parameters
    ----------
    neighbor_graph:
        Computed from `bicpl.PolygonObj.neighbor_graph`
    data:
        Vertex-wise data, typically produced from `depth_potential`
    """
    return (_local_da(n, data, i) for i, n in enumerate(neighbor_graph))
