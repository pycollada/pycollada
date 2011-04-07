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
from lxml import etree as ElementTree
import primitive
import types
import triangleset
import polylist
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag, E

class Polygons(polylist.Polylist):
    """Class containing the data COLLADA puts in a <polygons> tag, a collection of faces and holes."""

    def __init__(self, sources, material, polygons, xmlnode=None):
        """Create a set of polygons.

        :Parameters:
          sources
            A dict mapping source types to an array of tuples in the form:
            {input_type: (offset, semantic, sourceid, set, Source)}
            Example:
            {'VERTEX': [(0, 'VERTEX', '#vertex-inputs', '0', <collada.source.FloatSource>)]}
          material
            A string with the symbol of the material
          polygons
            A list of numpy arrays, each containing a set of indices to make a polygon
          xmlnode
            An xml node in case this is loaded from there

        """
        
        max_offset = max([ max([input[0] for input in input_type_array])
                          for input_type_array in sources.itervalues() if len(input_type_array) > 0])
        
        vcounts = numpy.zeros(len(polygons), dtype=numpy.int32)
        for i, poly in enumerate(polygons):
            vcounts[i] = len(poly) / (max_offset + 1)

        indices = numpy.concatenate(polygons)

        super(Polygons, self).__init__(sources, material, indices, vcounts, xmlnode)
        
        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            acclen = len(polygons) 

            self.xmlnode = E.polygons(count=str(acclen), material=self.material)
            
            all_inputs = []
            for semantic_list in self.sources.itervalues():
                all_inputs.extend(semantic_list)
            for offset, semantic, sourceid, set, src in all_inputs:
                inpnode = E.input(offset=str(offset), semantic=semantic, source=sourceid)
                if set is not None:
                    inpnode.set('set', str(set))
                self.xmlnode.append(inpnode)
            
            for poly in polygons:
                self.xmlnode.append(E.p(' '.join(str(f) for f in poly.flat)))

    @staticmethod
    def load( collada, localscope, node ):
        indexnodes = node.findall(tag('p'))
        if indexnodes is None: raise DaeIncompleteError('Missing indices in polygons')

        polygon_indices = []
        for indexnode in indexnodes:
            polygon_indices.append(numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' '))
        
        all_inputs = primitive.Primitive.getInputs(localscope, node.findall(tag('input')))

        polygons = Polygons(all_inputs, node.get('material'), polygon_indices, node)
        return polygons
    
    def bind(self, matrix, materialnodebysymbol):
        """Create a bound polygon list from this polygon list, transform and material mapping"""
        return BoundPolygons( self, matrix, materialnodebysymbol )

class BoundPolygons(polylist.BoundPolylist):
    """Polygons bound to a transform matrix and materials mapping."""

    def __init__(self, pl, matrix, materialnodebysymbol):
        """Create a BoundPolygons from a Polygons, transform and material mapping"""
        super(BoundPolygons, self).__init__(pl, matrix, materialnodebysymbol)
