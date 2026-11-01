####################################################################
#                                                                  #
# THIS FILE IS PART OF THE pycollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE pycollada SOURCE CODE IS (C) COPYRIGHT 2011                  #
# by Jeff Terrace and contributors                                 #
#                                                                  #
####################################################################

"""This module contains utility functions"""

import numpy
import math
from collections.abc import MutableSequence

from collada.common import DaeMalformedError, E, tag


def falmostEqual(a, b, rtol=1.0000000000000001e-05, atol=1e-08):
    """Checks if the given floats are almost equal. Uses the algorithm
    from numpy.allclose.

    :param float a:
      First float to compare
    :param float b:
      Second float to compare
    :param float rtol:
      The relative tolerance parameter
    :param float atol:
      The absolute tolerance parameter

    :rtype: bool

    """

    return math.fabs(a - b) <= (atol + rtol * math.fabs(b))


def toUnitVec(vec):
    """Converts the given vector to a unit vector

    :param numpy.array vec:
      The vector to transform to unit length

    :rtype: numpy.array

    """
    return vec / numpy.sqrt(numpy.vdot(vec, vec))


def checkSource(source, components, maxindex):
    """Check if a source objects complies with the needed `components` and has the needed length

    :param collada.source.Source source:
      A source instance to check
    :param tuple components:
      A tuple describing the needed channels, e.g. ``('X','Y','Z')``
    :param int maxindex:
      The maximum index that refers to this source

    """
    if len(source.data) <= maxindex:
        raise DaeMalformedError(
            "Indexes (maxindex=%d) for source '%s' (len=%d) go beyond the limits of the source"
            % (maxindex, source.id, len(source.data)))

    # some files will write sources with no named parameters
    # by spec, these params should just be skipped, but we need to
    # adapt to the failed output of others...
    if len(source.components) == len(components):
        source.components = components

    if source.components != components:
        raise DaeMalformedError('Wrong format in source %s' % source.id)
    return source


def normalize_v3(arr):
    """Normalize a numpy array of 3 component vectors with shape (N,3)

    :param numpy.array arr:
      The numpy array to normalize

    :rtype: numpy.array

    """
    lens = numpy.sqrt(arr[:, 0]**2 + arr[:, 1]**2 + arr[:, 2]**2)
    lens[numpy.equal(lens, 0)] = 1
    arr[:, 0] /= lens
    arr[:, 1] /= lens
    arr[:, 2] /= lens
    return arr


def dot_v3(arr1, arr2):
    """Calculates the dot product for each vector in two arrays

    :param numpy.array arr1:
      The first array, shape Nx3
    :param numpy.array arr2:
      The second array, shape Nx3

    :rtype: numpy.array

    """
    return arr1[:, 0] * arr2[:, 0] + arr1[:, 1] * arr2[:, 1] + arr2[:, 2] * arr1[:, 2]


class IndexedList(MutableSequence):
    """A mutable sequence of objects with string lookups by their id attribute.

    Positional indexing and slicing follow list semantics. ID lookups use the
    last object with that ID. The cache is built lazily and invalidated by edits.
    """

    def __init__(self, items, attrs=('id',)):
        # Retain the existing id-only constructor calls used by Collada.
        if tuple(attrs) != ('id',):
            raise ValueError('IndexedList indexes the id attribute only')
        self._items = list(items)
        self._by_id = None

    def _index(self):
        if self._by_id is None:
            self._by_id = {item.id: item for item in self._items}
        return self._by_id

    def _position(self, key):
        if isinstance(key, str):
            return self._items.index(self._index()[key])
        return key

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._index()[key]
        if isinstance(key, slice):
            return IndexedList(self._items[key])
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[self._position(key)] = value
        self._by_id = None

    def __delitem__(self, key):
        del self._items[self._position(key)]
        self._by_id = None

    def insert(self, index, value):
        self._items.insert(self._position(index), value)
        self._by_id = None

    def append(self, value):
        if self._by_id is not None:
            key = value.id
            hash(key)
        self._items.append(value)
        if self._by_id is not None:
            self._by_id[key] = value

    def extend(self, values):
        # Snapshot self-extension and iterators before mutating the sequence.
        values = list(values)
        if self._by_id is not None:
            additions = {value.id: value for value in values}
        self._items.extend(values)
        if self._by_id is not None:
            self._by_id.update(additions)

    def get(self, key, default=None):
        return self._index().get(key, default)

    def __contains__(self, value):
        if isinstance(value, str):
            return value in self._index()
        return value in self._items

    def __eq__(self, other):
        if isinstance(other, IndexedList):
            return self._items == other._items
        if isinstance(other, list):
            return self._items == other
        return NotImplemented


def _correctValInNode(outernode, tagname, value):
    innernode = outernode.find(tag(tagname))
    if value is None and innernode is not None:
        outernode.remove(innernode)
    elif innernode is not None:
        innernode.text = str(value)
    elif value is not None:
        outernode.append(E(tagname, str(value)))
