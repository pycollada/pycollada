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

"""Module containing classes and functions for the <triangles> primitive."""

import numpy
from lxml import etree as ElementTree
import primitive
import types
from util import toUnitVec, checkSource, normalize_v3
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag, E

class Triangle(object):
    """Single triangle representation."""
    def __init__(self, indices, vertices, normals, texcoords, material):
        """A triangle should not be created manually."""

        self.vertices = vertices
        """A (3, 3) float array for points in the triangle"""
        self.normals = normals
        """A (3, 3) float array with the normals for points in the triangle.
        If the triangle didn't have normals, they will be computed."""
        self.texcoords = texcoords
        """A tuple with (3, 2) float arrays with the texture coordinates
          for the points in the triangle"""
        self.material = material
        """If coming from an unbound :class:`collada.triangleset.TriangleSet`, contains a
          string with the material symbol. If coming from a bound
          :class:`collada.triangleset.BoundTriangleSet`, contains the actual
          :class:`collada.material.Effect` the triangle is bound to."""
        self.indices = indices
        """A (3, 3) int array with vertex indexes in the vertex array"""

        if self.normals is None:
            #generate normals
            vec1 = numpy.subtract(vertices[0], vertices[1])
            vec2 = numpy.subtract(vertices[2], vertices[0])
            vec3 = toUnitVec(numpy.cross(toUnitVec(vec2), toUnitVec(vec1)))
            self.normals = numpy.array([vec3, vec3, vec3])

    def __repr__(self): 
        return '<Triangle (%s, %s, %s, "%s")>'%(str(self.vertices[0]), str(self.vertices[1]), 
                                             str(self.vertices[2]), str(self.material))
    def __str__(self): return repr(self)

class TriangleSet(primitive.Primitive):
    """Class containing the data COLLADA puts in a <triangles> tag, a collection of
    triangles.
    
    * The TriangleSet object is read-only. To modify a TriangleSet, create a new
      instance using :meth:`collada.geometry.Geometry.createTriangleSet`.
    * If ``T`` is an instance of :class:`collada.triangleset.TriangleSet`, then ``len(T)``
      returns the number of triangles in the set. ``T[i]`` returns the i\ :sup:`th`
      triangle in the set.
    """

    def __init__(self, sources, material, index, xmlnode=None):
        """A TriangleSet should not be created manually. Instead, call the
        :meth:`collada.geometry.Geometry.createTriangleSet` method after
        creating a geometry instance.
        """

        if len(sources) == 0: raise DaeIncompleteError('A triangle set needs at least one input for vertex positions')
        if not 'VERTEX' in sources: raise DaeIncompleteError('Triangle set requires vertex input')

        max_offset = max([ max([input[0] for input in input_type_array])
                          for input_type_array in sources.itervalues() if len(input_type_array) > 0])

        self.material = material
        self.index = index
        self.indices = self.index
        self.nindices = max_offset + 1
        self.index.shape = (-1, 3, self.nindices)
        self.ntriangles = len(self.index)
        self.sources = sources

        if len(self.index) > 0:
            self._vertex = sources['VERTEX'][0][4].data
            self._vertex_index = self.index[:,:, sources['VERTEX'][0][0]]
            self.maxvertexindex = numpy.max( self._vertex_index )
            checkSource(sources['VERTEX'][0][4], ('X', 'Y', 'Z'), self.maxvertexindex)
        else:
            self._vertex = None
            self._vertex_index = None
            self.maxvertexindex = -1

        if 'NORMAL' in sources and len(sources['NORMAL']) > 0 and len(self.index) > 0:
            self._normal = sources['NORMAL'][0][4].data
            self._normal_index = self.index[:,:, sources['NORMAL'][0][0]]
            self.maxnormalindex = numpy.max( self._normal_index )
            checkSource(sources['NORMAL'][0][4], ('X', 'Y', 'Z'), self.maxnormalindex)
        else:
            self._normal = None
            self._normal_index = None
            self.maxnormalindex = -1
            
        if 'TEXCOORD' in sources and len(sources['TEXCOORD']) > 0 and len(self.index) > 0:
            self._texcoordset = tuple([texinput[4].data for texinput in sources['TEXCOORD']])
            self._texcoord_indexset = tuple([ self.index[:,:, sources['TEXCOORD'][i][0]]
                                             for i in xrange(len(sources['TEXCOORD'])) ])
            self.maxtexcoordsetindex = [ numpy.max( tex_index ) for tex_index in self._texcoord_indexset ]
            for i, texinput in enumerate(sources['TEXCOORD']):
                checkSource(texinput[4], ('S', 'T'), self.maxtexcoordsetindex[i])
        else:
            self._texcoordset = tuple()
            self._texcoord_indexset = tuple()
            self.maxtexcoordsetindex = -1
            
        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            self.index.shape = (-1)
            acclen = len(self.index)
            txtindices = ' '.join([str(i) for i in self.index])
            self.index.shape = (-1, 3, self.nindices)
            
            self.xmlnode = E.triangles(count=str(self.ntriangles), material=self.material)
            
            all_inputs = []
            for semantic_list in self.sources.itervalues():
                all_inputs.extend(semantic_list)
            for offset, semantic, sourceid, set, src in all_inputs:
                inpnode = E.input(offset=str(offset), semantic=semantic, source=sourceid)
                if set is not None:
                    inpnode.set('set', str(set))
                self.xmlnode.append(inpnode)
            
            self.xmlnode.append(E.p(txtindices))

    def __len__(self): return len(self.index)

    def __getitem__(self, i):
        v = self._vertex[ self._vertex_index[i] ]
        n = self._normal[ self._normal_index[i] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[i] ] )
        return Triangle(self._vertex_index[i], v, n, uv, self.material)

    @staticmethod
    def load( collada, localscope, node ):
        indexnode = node.find(tag('p'))
        if indexnode is None: raise DaeIncompleteError('Missing index in triangle set')
        
        source_array = primitive.Primitive._getInputs(localscope, node.findall(tag('input')))
            
        try:
            if indexnode.text is None:
                index = numpy.array([], dtype=numpy.int32)
            else:
                index = numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' ')
        except: raise DaeMalformedError('Corrupted index in triangleset')
        
        triset = TriangleSet(source_array, node.get('material'), index, node)
        triset.xmlnode = node
        return triset
    
    def bind(self, matrix, materialnodebysymbol):
        """Create a bound triangle set from this triangle set, transform and material mapping"""
        return BoundTriangleSet( self, matrix, materialnodebysymbol)

    def __str__(self): return '<TriangleSet length=%d>' % len(self)
    def __repr__(self): return str(self)

class BoundTriangleSet(primitive.BoundPrimitive):
    """A triangle set bound to a transform matrix and materials mapping.
    
    * If ``T`` is an instance of :class:`collada.triangleset.BoundTriangleSet`, then ``len(T)``
      returns the number of triangles in the set. ``T[i]`` returns the i\ :sup:`th`
      triangle in the set.
    """

    def __init__(self, ts, matrix, materialnodebysymbol):
        """Create a bound triangle set from a triangle set, transform and material mapping.
        This gets created when a triangle set is instantiated in a scene. Do not create this manually."""
        M = numpy.asmatrix(matrix).transpose()
        self._vertex = None if ts.vertex is None else numpy.asarray(ts._vertex * M[:3,:3]) + matrix[:3,3]
        self._normal = None if ts._normal is None else numpy.asarray(ts._normal * M[:3,:3])
        self._texcoordset = ts._texcoordset
        matnode = materialnodebysymbol.get( ts.material )
        if matnode:
            self.material = matnode.target
            self.inputmap = dict([ (sem, (input_sem, set)) for sem, input_sem, set in matnode.inputs ])
        else: self.inputmap = self.material = None
        self.index = ts.index
        self._vertex_index = ts._vertex_index
        self._normal_index = ts._normal_index
        self._texcoord_indexset = ts._texcoord_indexset
        self.ntriangles = ts.ntriangles
        self.original = ts
    
    def __len__(self): return len(self.index)

    def __getitem__(self, i):
        v = self._vertex[ self._vertex_index[i] ]
        if self._normal is None:
            n = None
        else:
            n = self._normal[ self._normal_index[i] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[i] ] )
        return Triangle(self._vertex_index[i], v, n, uv, self.material)

    def triangles(self):
        """Iterate through all the triangles contained in the set.
        
        :rtype: generator of :class:`collada.triangleset.Triangle`
        """
        for i in xrange(self.ntriangles): yield self[i]

    def shapes(self):
        """Iterate through all the triangles contained in the set.
        
        :rtype: generator of :class:`collada.triangleset.Triangle`
        """
        return self.triangles()
    
    def generateNormals(self):
        """If :attr:`normals` is `None` or you wish for normals to be
        recomputed, call this method to recompute them."""
        norms = numpy.zeros( self._vertex.shape, dtype=self._vertex.dtype )
        tris = self._vertex[self._vertex_index]
        n = numpy.cross( tris[::,1] - tris[::,0], tris[::,2] - tris[::,0] )
        normalize_v3(n)
        norms[ self._vertex_index[:,0] ] += n
        norms[ self._vertex_index[:,1] ] += n
        norms[ self._vertex_index[:,2] ] += n
        normalize_v3(norms)
        
        self._normal = norms
        self._normal_index = self._vertex_index

    def __str__(self): return '<BoundTriangleSet length=%d>' % len(self)
    def __repr__(self): return str(self)
    