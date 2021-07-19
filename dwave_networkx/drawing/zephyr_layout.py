# Copyright 2021 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
Tools to visualize Zephyr lattices and weighted graph problems on them.
"""

import networkx as nx
from networkx import draw

from dwave_networkx.drawing.qubit_layout import draw_qubit_graph, draw_embedding, draw_yield
from dwave_networkx.generators.zephyr import zephyr_graph, zephyr_coordinates


__all__ = ['zephyr_layout',
           'draw_zephyr',
           'draw_zephyr_embedding',
           'draw_zephyr_yield',
           ]


def zephyr_layout(G, scale=1., center=None, dim=2):
    """Positions the nodes of graph G in a Zephyr topology.

    `NumPy <https://scipy.org>`_ is required for this function.

    Parameters
    ----------
    G : NetworkX graph
        A Zephyr graph or a subgraph of a Zephyr graph, as produced by
        the :func:`dwave_networkx.zephyr_graph` function.

    scale : float (default 1.)
        Scale factor. A setting of ``scale = 1`` fits all positions within
        [0, 1] on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    Returns
    -------
    pos : dict
        Positions as a dictionary keyed by node.

    Examples
    --------
        This example gives the positions of a Zephyr lattice of size 2.

    >>> G = dnx.zephyr_graph(2)
    >>> pos = dnx.zephyr_layout(G)

    """

    if not isinstance(G, nx.Graph) or G.graph.get("family") != "zephyr":
        raise ValueError("G must be generated by dwave_networkx.zephyr_graph")

    xy_coords = zephyr_node_placer_2d(G, scale, center, dim)

    if G.graph.get('labels') == 'coordinate':
        pos = {v: xy_coords(*v) for v in G.nodes()}
    elif G.graph.get('data'):
        pos = {v: xy_coords(*dat['zephyr_index']) for v, dat in G.nodes(data=True)}
    else:
        m = G.graph.get('rows')
        t = G.graph.get('tile')
        coord = zephyr_coordinates(m, t)
        pos = {v: xy_coords(*coord.linear_to_zephyr(v)) for v in G.nodes()}

    return pos


def zephyr_node_placer_2d(G, scale=1., center=None, dim=2):
    """Generates a function to convert Zephyr indices to plottable coordinates.

    Parameters
    ----------
    G : NetworkX graph
        A Zephyr graph or a subgraph of a Zephyr graph, as produced by
        the :func:`dwave_networkx.zephyr_graph` function.

    scale : float (default 1.)
        Scale factor. A setting of ``scale = 1`` fits all positions within
        [0, 1] on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    Returns
    -------
    xy_coords : function
        A function that maps a Zephyr index (u, w, k, j, z) in a
        Zephyr lattice to plottable x,y coordinates.

    """
    import numpy as np

    m = G.graph.get('rows')
    tile_width = G.graph.get("tile")

    # want the enter plot to fill in [0, 1] when scale=1
    scale /= m * tile_width

    if center is None:
        center = np.zeros(dim)
    else:
        center = np.asarray(center)

    paddims = dim - 2
    if paddims < 0:
        raise ValueError("layout must have at least two dimensions")

    if len(center) != dim:
        raise ValueError("length of center coordinates must match dimension of layout")

    def _xy_coords(u, w, k, j, z):
        # orientation, major perpendicular offset, secondary perpendicular offset, minor perpendicular offset, parallel offset
        W = 2*tile_width*w + 2*k + .625*j + .125
        Z = (2*z+j+1)*2*tile_width - .5

        if u:
            xy = np.array([W, -Z])
        else:
            xy = np.array([Z, -W])

        return np.hstack((xy * scale, np.zeros(paddims))) + center

    return _xy_coords


def draw_zephyr(G, **kwargs):
    """Draws graph G in a Zephyr topology.

    If ``linear_biases`` and/or ``quadratic_biases`` are provided, these
    are visualized on the plot.

    Parameters
    ----------
    G : NetworkX graph
        A Zephyr graph or a subgraph of a Zephyr graph, as produced by
        the :func:`dwave_networkx.zephyr_graph` function.

    linear_biases : dict (optional, default {})
        Biases as a dict, of form {node: bias, ...}, where keys are
        nodes in G and biases are numeric.

    quadratic_biases : dict (optional, default {})
        Biases as a dict, of form {edge: bias, ...}, where keys are
        edges in G and biases are numeric. Self-loop
        edges (i.e., :math:`i=j`) are treated as linear biases.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the ``pos`` parameter, which is not used by this
       function. If ``linear_biases`` or ``quadratic_biases`` are provided,
       any provided ``node_color`` or ``edge_color`` arguments are ignored.

    Examples
    --------
        This example plots a Zephyr graph with size parameter 2.

    >>> import networkx as nx
    >>> import dwave_networkx as dnx
    >>> import matplotlib.pyplot as plt   # doctest: +SKIP
    >>> G = dnx.zephyr_graph(2)
    >>> dnx.draw_zephyr(G)    # doctest: +SKIP
    >>> plt.show()    # doctest: +SKIP

    """

    draw_qubit_graph(G, zephyr_layout(G), **kwargs)


def draw_zephyr_embedding(G, *args, **kwargs):
    """Draws an embedding onto Zephyr graph G.

    Parameters
    ----------
    G : NetworkX graph
        A Zephyr graph or a subgraph of a Zephyr graph, as produced by
        the :func:`dwave_networkx.zephyr_graph` function.

    emb : dict
        Chains, as a dict of form {qubit: chain, ...}, where qubits are
        nodes in G and chains are iterables of qubit labels.

    embedded_graph : NetworkX graph (optional, default None)
        A graph that contains all keys of ``emb`` as nodes.  If specified,
        edges of G are considered interactions if and only if (1) they
        exist between two chains of ``emb`` and (2) their keys are connected
        by an edge in this graph. If given, only couplers between chains
        based on this graph are displayed.

    interaction_edges : list (optional, default None)
        A list of edges used as interactions. If given,
        only these couplers are displayed.

    show_labels: boolean (optional, default False)
        If True, each chain in ``emb`` is labelled with its key.

    chain_color : dict (optional, default None)
        Colors as a dict of form {node: rgba_color, ...} associated with
        each key in ``emb``, where colors are length-4 tuples of floats
        between 0 and 1 inclusive. If None, each chain is assigned a
        different color.

    unused_color : tuple (optional, default (0.9,0.9,0.9,1.0))
        Color for nodes of G that are not part of chains, and edges
        that are neither chain edges nor interactions. If None, these
        nodes and edges are not shown.

    overlapped_embedding: boolean (optional, default False)
        If True, chains in ``emb`` may overlap (contain the same vertices
        in G), and these overlaps are displayed as concentric circles.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the ``pos`` parameter, which is not used by this
       function. If ``linear_biases`` or ``quadratic_biases`` are provided,
       any provided ``node_color`` or ``edge_color`` arguments are ignored.
    """
    draw_embedding(G, zephyr_layout(G), *args, **kwargs)

def draw_zephyr_yield(G, **kwargs):
    """Draws the given graph G with highlighted faults, according to layout.

    Parameters
    ----------
    G : NetworkX graph
        Graph to be parsed for faults.

    unused_color : tuple or color string (optional, default (0.9,0.9,0.9,1.0))
        The color to use for nodes and edges of G which are not faults.
        If unused_color is None, these nodes and edges will not be shown at all.

    fault_color : tuple or color string (optional, default (1.0,0.0,0.0,1.0))
        A color to represent nodes absent from the graph G. Colors should be
        length-4 tuples of floats between 0 and 1 inclusive.

    fault_shape : string, optional (default='x')
        The shape of the fault nodes. Specification is as matplotlib.scatter
        marker, one of 'so^>v<dph8'.

    fault_style : string, optional (default='dashed')
        Edge fault line style (solid|dashed|dotted,dashdot)

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the `pos` parameter which is not used by this
       function. If `linear_biases` or `quadratic_biases` are provided,
       any provided `node_color` or `edge_color` arguments are ignored.
    """
    try:
        assert(G.graph["family"] == "zephyr")
        m = G.graph['columns']
        t = G.graph['tile']
        coordinates = G.graph["labels"] == "coordinate"
        # Can't interpret fabric_only from graph attributes
    except:
        raise ValueError("Target zephyr graph needs to have columns, rows, \
        tile, and label attributes to be able to identify faulty qubits.")


    perfect_graph = zephyr_graph(m, t, coordinates=coordinates)

    draw_yield(G, zephyr_layout(perfect_graph), perfect_graph, **kwargs)
