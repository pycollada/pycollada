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

"""Module containing classes and functions for the <polylist> primitive."""

import numpy
from lxml import etree as ElementTree
import primitive
import types
import triangleset
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag, E

class Polygon(object):
    """Single polygon representation."""
    def __init__(self, indices, vertices, normals, texcoords, material):
        """Create a polygon from numpy arrays.

        :Parameters:
          indices
            A (3,) int array with vertex indexes in the vertex array.
          vertices
            A (N, 3) float array for points in the polygon.
          normals
            A (N, 3) float array with the normals for points in the polygon. Can be None.
          texcoords
            A tuple with (N, 2) float arrays with the texcoords for points.
          material
            If coming from a not bound set, a symbol (string),
            otherwise, the material object itself.

        """
        self.vertices = vertices
        """A (N, 3) float array for points in the polygon."""
        self.normals = normals
        """A (N, 3) float array with the normals for points in the polygon. Can be None."""
        self.texcoords = texcoords
        """A tuple with (N, 2) float arrays with the texcoords for points.."""
        self.material = material
        """Symbol (string) or the material object itself if bound."""
        self.indices = indices

    def triangles(self):
        """Generates triangle objects from this polygon"""
        
        npts = len(self.vertices)

        for i in range(npts-2):
            
            tri_indices = numpy.array([
                self.indices[0], self.indices[i+1], self.indices[i+2]
                ])
            
            tri_vertices = numpy.array([
                self.vertices[0], self.vertices[i+1], self.vertices[i+2]
                ])
            
            if self.normals is None:
                tri_normals = None
            else:
                tri_normals = numpy.array([
                    self.normals[0], self.normals[i+1], self.normals[i+2]
                    ])
            
            tri_texcoords = []
            for texcoord in self.texcoords:
                tri_texcoords.append([texcoord[0], texcoord[i+1], texcoord[i+2]])
            tri_texcoords = numpy.array(tri_texcoords)
            
            tri = triangleset.Triangle(tri_indices, tri_vertices, tri_normals, tri_texcoords, self.material)
            yield tri

    def __repr__(self): 
        return 'Polygon (vertices=%d)' % len(self.vertices)
    def __str__(self): return repr(self)

class Polylist(primitive.Primitive):
    """Class containing the data COLLADA puts in a <polylist> tag, a collection of faces."""

    def __init__(self, sources, material, index, vcounts, xmlnode=None):
        """Create a polygon list.

        :Parameters:
          sources
            A dict mapping source types to an array of tuples in the form:
            {input_type: (offset, semantic, sourceid, set, Source)}
            Example:
            {'VERTEX': [(0, 'VERTEX', '#vertex-inputs', '0', <collada.source.FloatSource>)]}
          material
            A string with the symbol of the material
          index
            An array with the indexes as they come from the collada file
          vcounts
            A list with the lengths of each individual polygon
          xmlnode
            An xml node in case this is loaded from there

        """
        
        if len(sources) == 0: raise DaeIncompleteError('A polylist set needs at least one input for vertex positions')
        if not 'VERTEX' in sources: raise DaeIncompleteError('Polylist requires vertex input')

        #find max offset
        max_offset = max([ max([input[0] for input in input_type_array])
                          for input_type_array in sources.itervalues() if len(input_type_array) > 0])

        self.material = material
        self.index = index
        self.indices = self.index
        self.nindices = max_offset + 1
        self.vcounts = vcounts
        self.sources = sources
        self.index.shape = (-1, self.nindices)
        self.npolygons = len(self.vcounts)
        self.nvertices = numpy.sum(self.vcounts) if len(self.index) > 0 else 0
        self.polyends = numpy.cumsum(self.vcounts)
        self.polystarts = self.polyends - self.vcounts
        self.polyindex = numpy.dstack((self.polystarts, self.polyends))[0]

        if len(self.index) > 0:
            self._vertex = sources['VERTEX'][0][4].data
            self._vertex_index = self.index[:,sources['VERTEX'][0][0]]
            self.maxvertexindex = numpy.max( self._vertex_index )
            checkSource(sources['VERTEX'][0][4], ('X', 'Y', 'Z'), self.maxvertexindex)
        else:
            self._vertex = None
            self._vertex_index = None
            self.maxvertexindex = -1

        if 'NORMAL' in sources and len(sources['NORMAL']) > 0 and len(self.index) > 0:
            self._normal = sources['NORMAL'][0][4].data
            self._normal_index = self.index[:,sources['NORMAL'][0][0]]
            self.maxnormalindex = numpy.max( self._normal_index )
            checkSource(sources['NORMAL'][0][4], ('X', 'Y', 'Z'), self.maxnormalindex)
        else:
            self._normal = None
            self._normal_index = None
            self.maxnormalindex = -1
            
        if 'TEXCOORD' in sources and len(sources['TEXCOORD']) > 0 and len(self.index) > 0:
            self._texcoordset = tuple([texinput[4].data for texinput in sources['TEXCOORD']])
            self._texcoord_indexset = tuple([ self.index[:,sources['TEXCOORD'][i][0]]
                                             for i in xrange(len(sources['TEXCOORD'])) ])
            self.maxtexcoordsetindex = [ numpy.max(each) for each in self._texcoord_indexset ]
            for i, texinput in enumerate(sources['TEXCOORD']):
                checkSource(texinput[4], ('S', 'T'), self.maxtexcoordsetindex[i])
        else:
            self._texcoordset = tuple()
            self._texcoord_indexset = tuple()
            self.maxtexcoordsetindex = -1
            
        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            txtindices = ' '.join(str(f) for f in self.indices.flat)
            acclen = len(self.indices) 

            self.xmlnode = E.polylist(count=str(self.npolygons), material=self.material)
            
            all_inputs = []
            for semantic_list in self.sources.itervalues():
                all_inputs.extend(semantic_list)
            for offset, semantic, sourceid, set, src in all_inputs:
                inpnode = E.input(offset=str(offset), semantic=semantic, source=sourceid)
                if set is not None:
                    inpnode.set('set', str(set))
                self.xmlnode.append(inpnode)
            
            vcountnode = E.vcount(' '.join(str(v) for v in self.vcounts))
            self.xmlnode.append(vcountnode)
            self.xmlnode.append(E.p(txtindices))

    def __len__(self): return self.npolygons

    def __getitem__(self, i):
        polyrange = self.polyindex[i]
        vertindex = self._vertex_index[polyrange[0]:polyrange[1]]
        v = self._vertex[vertindex]
        if self.normal is None:
            n = None
        else:
            n = self._normal[ self._normal_index[polyrange[0]:polyrange[1]] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[polyrange[0]:polyrange[1]] ] )
        return Polygon(vertindex, v, n, uv, self.material)

    _triangleset = None
    def triangleset(self):
        if self._triangleset is None:
            indexselector = numpy.zeros(self.nvertices) == 0
            indexselector[self.polyindex[:,1]-1] = False
            indexselector[self.polyindex[:,1]-2] = False
            indexselector = numpy.arange(self.nvertices)[indexselector]
            
            firstpolyindex = numpy.arange(self.nvertices)
            firstpolyindex = firstpolyindex - numpy.repeat(self.polyends - self.vcounts, self.vcounts)
            firstpolyindex = firstpolyindex[indexselector]
            
            triindex = numpy.dstack( (self.index[indexselector-firstpolyindex],
                                      self.index[indexselector+1],
                                      self.index[indexselector+2]) )
            triindex = numpy.swapaxes(triindex, 1,2).flatten()
            
            triset = triangleset.TriangleSet(self.sources, self.material, triindex, self.xmlnode)
            
            self._triangleset = triset
        return self._triangleset

    @staticmethod
    def load( collada, localscope, node ):
        indexnode = node.find(tag('p'))
        if indexnode is None: raise DaeIncompleteError('Missing index in polylist')
        vcountnode = node.find(tag('vcount'))
        if vcountnode is None: raise DaeIncompleteError('Missing vcount in polylist')

        try:
            if vcountnode.text is None:
                vcounts = numpy.array([], dtype=numpy.int32)
            else:
                vcounts = numpy.fromstring(vcountnode.text, dtype=numpy.int32, sep=' ')
        except ValueError, ex: raise DaeMalformedError('Corrupted vcounts in polylist')

        all_inputs = primitive.Primitive.getInputs(localscope, node.findall(tag('input')))

        try:
            if indexnode.text is None:
                index = numpy.array([], dtype=numpy.int32)
            else:
                index = numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' ')
        except: raise DaeMalformedError('Corrupted index in polylist')

        polylist = Polylist(all_inputs, node.get('material'), index, vcounts, node)
        return polylist
    
    def bind(self, matrix, materialnodebysymbol):
        """Create a bound polygon list from this polygon list, transform and material mapping"""
        return BoundPolylist( self, matrix, materialnodebysymbol)

class BoundPolylist(primitive.BoundPrimitive):
    """A polygon set bound to a transform matrix and materials mapping."""

    def __init__(self, pl, matrix, materialnodebysymbol):
        """Create a bound polygon list from a polygon list, transform and material mapping"""
        M = numpy.asmatrix(matrix).transpose()
        self._vertex = None if pl._vertex is None else numpy.asarray(pl._vertex * M[:3,:3]) + matrix[:3,3]
        self._normal = None if pl._normal is None else numpy.asarray(pl._normal * M[:3,:3])
        self._texcoordset = pl._texcoordset
        matnode = materialnodebysymbol.get( pl.material )
        if matnode:
            self.material = matnode.target
            self.inputmap = dict([ (sem, (input_sem, set)) for sem, input_sem, set in matnode.inputs ])
        else: self.inputmap = self.material = None
        self.index = pl.index
        self.nvertices = pl.nvertices
        self._vertex_index = pl._vertex_index
        self._normal_index = pl._normal_index
        self._texcoord_indexset = pl._texcoord_indexset
        self.polyindex = pl.polyindex
        self.npolygons = pl.npolygons
        self.matrix = matrix
        self.materialnodebysymbol = materialnodebysymbol
        self.original = pl
    
    def __len__(self): return len(self.index)

    def __getitem__(self, i):
        polyrange = self.polyindex[i]
        vertindex = self._vertex_index[polyrange[0]:polyrange[1]]
        v = self._vertex[vertindex]
        if self.normal is None:
            n = None
        else:
            n = self._normal[ self._normal_index[polyrange[0]:polyrange[1]] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[polyrange[0]:polyrange[1]] ] )
        return Polygon(vertindex, v, n, uv, self.material)

    _triangleset = None
    def triangleset(self):
        if self._triangleset is None:
            triset = self.original.triangleset()
            boundtriset = triset.bind(self.matrix, self.materialnodebysymbol)
            self._triangleset = boundtriset
        return self._triangleset

    def polygons(self):
        """Iterate through all the polygons contained in the set."""
        for i in xrange(self.npolygons): yield self[i]

    def shapes(self):
        """Iterate through all the primitives contained in the set."""
        return self.polygons()
    
    vertex = property( lambda s: s._vertex )
    normal = property( lambda s: s._normal )
    texcoordset = property( lambda s: s._texcoordset )
    vertex_index = property( lambda s: s._vertex_index )
    normal_index = property( lambda s: s._normal_index )
    texcoord_indexset = property( lambda s: s._texcoord_indexset )
