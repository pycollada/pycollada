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

"""Module containing classes and functions for the <polygons> primitive."""

import numpy

from collada import primitive
from collada import polylist
from collada import triangleset
from collada.common import E, tag
from collada.common import DaeIncompleteError, DaeBrokenRefError, \
        DaeMalformedError, DaeUnsupportedError
from collada.util import toUnitVec, checkSource
from collada.xmlutil import etree as ElementTree


class Polygons(polylist.Polylist):
    """Class containing the data COLLADA puts in a <polygons> tag, a collection of
    polygons that can have holes.

    * The Polygons object is read-only. To modify a
      Polygons, create a new instance using :meth:`collada.geometry.Geometry.createPolygons`.

    * Polygons with holes are not currently supported, so for right now, this class is
      essentially the same as a :class:`collada.polylist.Polylist`. Use a polylist instead
      if your polygons don't have holes.
    """

    def __init__(self, sources, material, polygons, xmlnode=None):
        """A Polygons should not be created manually. Instead, call the
        :meth:`collada.geometry.Geometry.createPolygons` method after
        creating a geometry instance.
        """

        max_offset = max([ max([input[0] for input in input_type_array])
            for input_type_array in sources.values()
            if len(input_type_array) > 0])

        vcounts = numpy.zeros(len(polygons), dtype=numpy.int32)
        for i, poly in enumerate(polygons):
            vcounts[i] = len(poly) / (max_offset + 1)

        if len(polygons) > 0:
            indices = numpy.concatenate(polygons)
        else:
            indices = numpy.array([], dtype=numpy.int32)

        super(Polygons, self).__init__(sources, material, indices, vcounts, xmlnode)

        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            acclen = len(polygons)

            self.xmlnode = E.polygons(count=str(acclen), material=self.material)

            all_inputs = []
            for semantic_list in self.sources.values():
                all_inputs.extend(semantic_list)
            for offset, semantic, sourceid, set, src in all_inputs:
                inpnode = E.input(offset=str(offset), semantic=semantic, source=sourceid)
                if set is not None:
                    inpnode.set('set', str(set))
                self.xmlnode.append(inpnode)

            for poly in polygons:
                self.xmlnode.append(E.p(' '.join(map(str, poly.flatten().tolist()))))

    @staticmethod
    def load( collada, localscope, node ):
        indexnodes = node.findall(tag('p'))
        if indexnodes is None: raise DaeIncompleteError('Missing indices in polygons')

        polygon_indices = []
        for indexnode in indexnodes:
            index = numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' ')
            index[numpy.isnan(index)] = 0
            polygon_indices.append(index)

        all_inputs = primitive.Primitive._getInputs(collada, localscope, node.findall(tag('input')))

        polygons = Polygons(all_inputs, node.get('material'), polygon_indices, node)
        return polygons

    def bind(self, matrix, materialnodebysymbol):
        """Create a bound polygons from this polygons, transform and material mapping"""
        return BoundPolygons( self, matrix, materialnodebysymbol )

    def __str__(self):
        return '<Polygons length=%d>' % len(self)

    def __repr__(self):
        return str(self)


class BoundPolygons(polylist.BoundPolylist):
    """Polygons bound to a transform matrix and materials mapping."""

    def __init__(self, pl, matrix, materialnodebysymbol):
        """Create a BoundPolygons from a Polygons, transform and material mapping"""
        super(BoundPolygons, self).__init__(pl, matrix, materialnodebysymbol)

    def __str__(self):
        return '<BoundPolygons length=%d>' % len(self)

    def __repr__(self):
        return str(self)

