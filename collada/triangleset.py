####################################################################
#                                                                  #
# THIS FILE IS PART OF THE PyCollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE PyCollada SOURCE CODE IS (C) COPYRIGHT 2009                  #
# by Scopia Visual Interfaces Systems http://www.scopia.es/        #
#                                                                  #
####################################################################

"""Module containing classes and functions for the <triangle> primitive."""

import numpy
from xml.etree import ElementTree
import primitive
import types
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag

class Triangle(object):
    """Single triangle representation."""
    def __init__(self, indices, vertices, normals, texcoords, material):
        """Create a triangle from numpy arrays.

        :Parameters:
          indices
            A (3,) int array with vertex indexes in the vertex array
          vertices
            A (3, 3) float array for points a b c
          normals
            A (3, 3) float array with the normals por points a b c
          texcoords
            A tuple with (3, 2) float arrays with the texcoords for points 
            a b c
          material
            If coming from a not bound set, a symbol (string),
            otherwise, the material object itself

        """
        self.vertices = vertices
        """A (3, 3) float array for points a b c."""
        self.normals = normals
        """A (3, 3) float array with the normals for points a b c."""
        self.texcoords = texcoords
        """A tuple with (3, 2) float arrays with the texcoords."""
        self.material = material
        """Symbol (string) or the material object itself if bound."""
        self.indices = indices

        if self.normals is None:
            #generate normals
            vec1 = numpy.subtract(vertices[0], vertices[1])
            vec2 = numpy.subtract(vertices[2], vertices[0])
            vec3 = toUnitVec(numpy.cross(toUnitVec(vec2), toUnitVec(vec1)))
            self.normals = numpy.array([vec3, vec3, vec3])

    def __repr__(self): 
        return 'Triangle(%s, %s, %s, "%s")'%(str(self.vertices[0]), str(self.vertices[1]), 
                                             str(self.vertices[2]), str(self.material))
    def __str__(self): return repr(self)

class TriangleSet(primitive.Primitive):
    """Class containing the data COLLADA puts in a <triangle> tag, a collection of faces."""

    def __init__(self, sources, material, index, xmlnode=None):
        """Create a triangle set.

        :Parameters:
          sources
            A dict mapping source types to an array of tuples in the form:
            {input_type: (offset, semantic, sourceid, set, Source)}
            Example:
            {'VERTEX': (0, 'VERTEX', '#vertex-inputs', '0', <collada.source.FloatSource>)}
          material
            A string with the symbol of the material
          index
            An array with the indexes as they come from the collada file
          xmlnode
            An xml node in case this is loaded from there

        """

        if len(sources) == 0: raise DaeIncompleteError('A triangle set needs at least one input for vertex positions')
        if not 'VERTEX' in sources: raise DaeIncompleteError('Triangleset requires vertex input')

        #find max offset
        max_offset = max([ max([input[0] for input in input_type_array])
                          for input_type_array in sources.itervalues() if len(input_type_array) > 0])

        self.material = material
        self.index = index
        self.indices = self.index
        self.nindices = max_offset + 1
        self.index.shape = (-1, 3, self.nindices)
        self.ntriangles = len(self.index)

        self._vertex = sources['VERTEX'][0][4].data
        self._vertex_index = self.index[:,:, sources['VERTEX'][0][0]]
        self.maxvertexindex = numpy.max( self._vertex_index )
        checkSource(sources['VERTEX'][0][4], ('X', 'Y', 'Z'), self.maxvertexindex)

        if 'NORMAL' in sources and len(sources['NORMAL']) > 0:
            self._normal = sources['NORMAL'][0][4].data
            self._normal_index = self.index[:,:, sources['NORMAL'][0][0]]
            self.maxnormalindex = numpy.max( self._normal_index )
            checkSource(sources['NORMAL'][0][4], ('X', 'Y', 'Z'), self.maxnormalindex)
        else:
            self._normal = None
            self._normal_index = None
            self.maxnormalindex = -1
            
        if 'TEXCOORD' in sources and len(sources['TEXCOORD']) > 0:
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
            
        if xmlnode: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.fromstring("<triangles> <p></p> </triangles>")

    def __len__(self): return len(self.index)

    vertex = property( lambda s: s._vertex )
    """Read only vertex array, shape=(nv,3)."""
    normal = property( lambda s: s._normal )
    """Read only normal array, shape=(nn,3)."""
    texcoordset = property( lambda s: s._texcoordset )
    """Read only tuple of texcoords arrays. shape=(nt,2)."""
    
    vertex_index = property( lambda s: s._vertex_index )
    """Indices per triangle for vertex array, shape=(n, 3)."""
    normal_index = property( lambda s: s._normal_index )
    """Indices per triangle for normal array, shape=(n, 3)."""
    texcoord_indexset = property( lambda s: s._texcoord_indexset )
    """A tuple of arrays of indices for texcoord arrays, shape=(n,3)."""

    def set_vertex_source(self, c):
        try: self._vertex = checkSource(self.sourceById[c], 
                                         ('X', 'Y', 'Z'), self.maxvertexindex).data
        except KeyError, ex: raise DaeBrokenRefError('Setting missing vertex source in triangle set')
        self._vertex_source = c
    
    def set_normal_source(self, c):
        try: self._normal = checkSource(self.sourceById[c],
                                         ('X', 'Y', 'Z'), self.maxnormalindex).data
        except KeyError, ex: raise DaeBrokenRefError('Setting missing normal source in triangle set')
        self._normal_source = c

    def set_texcoord_sourceset(self, t):
        if len(t) != len(self._texcoord_sourceset):
            raise DaeMalformedError('Wrong number of texcoord sources')
        try: self._texcoordset = tuple([ 
                    checkSource(self.sourceById[c], ('S', 'T'), 
                                 self.maxtexcoordsetindex[i]).data for i,c in enumerate(t)])
        except KeyError, ex: raise DaeBrokenRefError('Setting missing texcoord source in triangle set')
        self._texcoord_sourceset = tuple(t)

    vertex_source = property( lambda s: s._vertex_source, set_vertex_source )
    """Channel id (string) inside the parent geometry node to use as vertex."""
    normal_source = property( lambda s: s._normal_source, set_normal_source )
    """Channel id (string) inside the parent geometry node to use as normal."""
    texcoord_sourceset = property( lambda s: s._texcoord_sourceset, set_texcoord_sourceset )
    """Channel ids (tuple of strings) inside the parent geometry node to use as texcoords."""

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
        
        source_array = primitive.Primitive.getInputs(localscope, node.findall(tag('input')))
            
        try:
            index = numpy.array([float(v) for v in indexnode.text.split()], dtype=numpy.int32)
        except: raise DaeMalformedError('Corrupted index in triangleset')
        
        triset = TriangleSet(source_array, node.get('material'), index)
        triset.xmlnode = node
        return triset

    def getXmlInput(self, semantic, offset):
        """Return the xml node for the given input and create it if it isn't there."""
        for input in self.xmlnode.findall(tag('input')):
            if input.get('offset') == str(offset) and input.get('semantic') == semantic: 
                return input
        insertpoint = len(self.xmlnode) - 1
        input = ElementTree.Element('input')
        input.set('semantic', semantic)
        input.set('offset', str(offset))
        input.tail = '\n'
        if semantic == 'TEXCOORD': input.set('set', str(offset-2))
        self.xmlnode.insert(insertpoint, input)
        return input

    def save(self):
        vnode = self.getXmlInput('VERTEX', 0)
        nnode = self.getXmlInput('NORMAL', 1)
        vnode.set('source', '#'+self._vertex_source)
        nnode.set('source', '#'+self._normal_source)
        for i, source in enumerate( self._texcoord_sourceset ):
            node = self.getXmlInput('TEXCOORD', i+2)
            node.set('source', '#'+source)
        indexnode = self.xmlnode.find(tag('p'))
        indexnode.text = str(numpy.reshape(self.index, (-1,)))[1:-1]
        self.xmlnode.set('material', self.material)
        self.xmlnode.set('count', str(len(self.index)))
    
    def bind(self, matrix, materialnodebysymbol):
        """Create a bound triangle set from this triangle set, transform and material mapping"""
        return BoundTriangleSet( self, matrix, materialnodebysymbol)

class BoundTriangleSet(object):
    """A triangle set bound to a transform matrix and materials mapping."""

    def __init__(self, ts, matrix, materialnodebysymbol):
        """Create a bound triangle set from a triangle set, transform and material mapping"""
        M = numpy.asmatrix(matrix).transpose()
        self._vertex = numpy.asarray(ts._vertex * M[:3,:3]) + matrix[:3,3]
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
        """Iterate through all the triangles contained in the set."""
        for i in xrange(self.ntriangles): yield self[i]

    def shapes(self):
        """Iterate through all the primitives contained in the set."""
        return self.triangles()

    def texsource(self, input):
        """Return the UV source no. for the input symbol coming from a material"""
        if self.inputmap is None or input not in self.inputmap: return None
        sem, set = self.inputmap[input]
        assert sem == 'TEXCOORD' # we only support mapping to at the time
        return sel.setToTexcoord[set]
    
    vertex = property( lambda s: s._vertex )
    normal = property( lambda s: s._normal )
    texcoordset = property( lambda s: s._texcoordset )
    vertex_index = property( lambda s: s._vertex_index )
    normal_index = property( lambda s: s._normal_index )
    texcoord_indexset = property( lambda s: s._texcoord_indexset )
