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


class IndexedList(list):
    """
    Class that combines a list and a dict into a single class
     - Written by Hugh Bothwell (http://stackoverflow.com/users/33258/hugh-bothwell)
     - Original source available at:
          http://stackoverflow.com/questions/5332841/python-list-dict-property-best-practice/5334686#5334686
     - Modifications by Jeff Terrace
    Given an object, obj, that has a property x, this allows you to create an IndexedList like so:
       L = IndexedList([], ('x'))
       o = obj()
       o.x = 'test'
       L.append(o)
       L[0] # = o
       L['test'] # = o
    """

    def __init__(self, items, attrs):
        super(IndexedList, self).__init__(items)
        # do indexing
        self._attrs = tuple(attrs)
        self._index = {}
        _add = self._addindex
        for obj in self:
            _add(obj)

    def _index_items(self, items):
        return {getattr(obj, attr): obj for obj in items for attr in self._attrs}

    def _addindex(self, obj):
        self._index.update(self._index_items([obj]))

    def _replace_items(self, items):
        # Validate all keys before changing either representation.
        index = self._index_items(items)
        list.__setitem__(self, slice(None), items)
        self._index = index

    def _position(self, ind):
        if isinstance(ind, str):
            return list.index(self, self._index[ind])
        return ind

    def __delitem__(self, ind):
        items = list(self)
        del items[self._position(ind)]
        self._replace_items(items)

    def __delslice__(self, i, j):
        del self[i:j]

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            return IndexedList(list.__getitem__(self, ind), self._attrs)
        try:
            return self._index[ind]
        except (KeyError, TypeError):
            if isinstance(ind, str):
                raise
            return list.__getitem__(self, ind)

    def get(self, key, default=None):
        return self._index.get(key, default)

    def __contains__(self, item):
        try:
            if item in self._index:
                return True
        except TypeError:
            pass
        return list.__contains__(self, item)

    def __getslice__(self, i, j):
        return self[i:j]

    def __setitem__(self, ind, new_obj):
        items = list(self)
        items[self._position(ind)] = new_obj
        self._replace_items(items)

    def __setslice__(self, i, j, newItems):
        self[i:j] = newItems

    def append(self, obj):
        index = self._index_items([obj])
        list.append(self, obj)
        self._index.update(index)

    def extend(self, newList):
        items = list(newList)
        index = self._index_items(items)
        list.extend(self, items)
        self._index.update(index)

    def insert(self, ind, new_obj):
        items = list(self)
        items.insert(self._position(ind), new_obj)
        self._replace_items(items)

    def pop(self, ind=-1):
        items = list(self)
        obj = items.pop(self._position(ind))
        self._replace_items(items)
        return obj

    def remove(self, ind_or_obj):
        try:
            obj = self._index[ind_or_obj]
        except (KeyError, TypeError):
            obj = ind_or_obj
        items = list(self)
        items.remove(obj)
        self._replace_items(items)

    def clear(self):
        list.clear(self)
        self._index.clear()

    def __iadd__(self, items):
        self.extend(items)
        return self

    def __imul__(self, count):
        self._replace_items(list(self) * count)
        return self

    def reverse(self):
        self._replace_items(list(reversed(self)))

    def sort(self, *, key=None, reverse=False):
        items = list(self)
        items.sort(key=key, reverse=reverse)
        self._replace_items(items)


def _correctValInNode(outernode, tagname, value):
    innernode = outernode.find(tag(tagname))
    if value is None and innernode is not None:
        outernode.remove(innernode)
    elif innernode is not None:
        innernode.text = str(value)
    elif value is not None:
        outernode.append(E(tagname, str(value)))
