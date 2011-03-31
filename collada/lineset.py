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

"""Module containing classes and functions for the <lines> primitive."""

import numpy
from lxml import etree as ElementTree
import primitive
import types
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag, E

class Line(object):
    """Single line representation."""
    def __init__(self, indices, vertices, normals, texcoords, material):
        """Create a line from numpy arrays.

        :Parameters:
          indices
            A (2,) int array with vertex indexes in the vertex array
          vertices
            A (2, 3) float array for points a b c
          normals
            A (2, 3) float array with the normals for points a b c
          texcoords
            A tuple with (2, 2) float arrays with the texcoords for points 
            a b c
          material
            If coming from a not bound set, a symbol (string),
            otherwise, the material object itself

        """
        self.vertices = vertices
        """A (2, 3) float array for points a b c."""
        self.normals = normals
        """A (2, 3) float array with the normals por points a b c."""
        self.texcoords = texcoords
        """A tuple with (2, 2) float arrays with the texcoords."""
        self.material = material
        """Symbol (string) or the material object itself if bound."""
        self.indices = indices

        # Note: we can't generate normals for lines if there are none

    def __repr__(self): 
        return 'Line(%s, %s, "%s")'%(str(self.vertices[0]), str(self.vertices[1]), str(self.material))
    def __str__(self): return repr(self)

class LineSet(primitive.Primitive):
    """Class containing the data COLLADA puts in a <lines> tag, a collection of faces."""

    def __init__(self, sources, material, index, xmlnode=None):
        """Create a line set.

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
          xmlnode
            An xml node in case this is loaded from there

        """

        if len(sources) == 0: raise DaeIncompleteError('A line set needs at least one input for vertex positions')
        if not 'VERTEX' in sources: raise DaeIncompleteError('Line set requires vertex input')

        #find max offset
        max_offset = max([ max([input[0] for input in input_type_array])
                          for input_type_array in sources.itervalues() if len(input_type_array) > 0])

        self.sources = sources
        self.material = material
        self.index = index
        self.indices = self.index
        self.nindices = max_offset + 1
        self.index.shape = (-1, 2, self.nindices)
        self.nlines = len(self.index)

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
            self.index.shape = (-1, 2, self.nindices)
            
            self.xmlnode = E.lines(count=str(self.nlines), material=self.material)
            
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

    vertex = property( lambda s: s._vertex )
    """Read only vertex array, shape=(nv,3)."""
    normal = property( lambda s: s._normal )
    """Read only normal array, shape=(nn,3)."""
    texcoordset = property( lambda s: s._texcoordset )
    """Read only tuple of texcoords arrays. shape=(nt,2)."""
    
    vertex_index = property( lambda s: s._vertex_index )
    """Indices per line for vertex array, shape=(n, 2)."""
    normal_index = property( lambda s: s._normal_index )
    """Indices per line for normal array, shape=(n, 2)."""
    texcoord_indexset = property( lambda s: s._texcoord_indexset )
    """A tuple of arrays of indices for texcoord arrays, shape=(n,2)."""

    vertex_source = property( lambda s: s._vertex_source )
    """Channel id (string) inside the parent geometry node to use as vertex."""
    normal_source = property( lambda s: s._normal_source )
    """Channel id (string) inside the parent geometry node to use as normal."""
    texcoord_sourceset = property( lambda s: s._texcoord_sourceset )
    """Channel ids (tuple of strings) inside the parent geometry node to use as texcoords."""

    def __getitem__(self, i):
        v = self._vertex[ self._vertex_index[i] ]
        n = self._normal[ self._normal_index[i] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[i] ] )
        return Line(self._vertex_index[i], v, n, uv, self.material)

    @staticmethod
    def load( collada, localscope, node ):
        indexnode = node.find(tag('p'))
        if indexnode is None: raise DaeIncompleteError('Missing index in line set')
        
        source_array = primitive.Primitive.getInputs(localscope, node.findall(tag('input')))
            
        try:
            if indexnode.text is None:
                index = numpy.array([],  dtype=numpy.int32)
            else:
                index = numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' ')
        except: raise DaeMalformedError('Corrupted index in line set')
        
        lineset = LineSet(source_array, node.get('material'), index, node)
        lineset.xmlnode = node
        return lineset
    
    def bind(self, matrix, materialnodebysymbol):
        """Create a bound line set from this line set, transform and material mapping"""
        return BoundLineSet( self, matrix, materialnodebysymbol)

class BoundLineSet(object):
    """A line set bound to a transform matrix and materials mapping."""

    def __init__(self, ls, matrix, materialnodebysymbol):
        """Create a bound line set from a line set, transform and material mapping"""
        M = numpy.asmatrix(matrix).transpose()
        self._vertex = None if ls._vertex is None else numpy.asarray(ls._vertex * M[:3,:3]) + matrix[:3,3]
        self._normal = None if ls._normal is None else numpy.asarray(ls._normal * M[:3,:3])
        self._texcoordset = ls._texcoordset
        matnode = materialnodebysymbol.get( ls.material )
        if matnode:
            self.material = matnode.target
            self.inputmap = dict([ (sem, (input_sem, set)) for sem, input_sem, set in matnode.inputs ])
        else: self.inputmap = self.material = None
        self.index = ls.index
        self._vertex_index = ls._vertex_index
        self._normal_index = ls._normal_index
        self._texcoord_indexset = ls._texcoord_indexset
        self.nlines = ls.nlines
        self.original = ls
    
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
        return Line(self._vertex_index[i], v, n, uv, self.material)

    def lines(self):
        """Iterate through all the lines contained in the set."""
        for i in xrange(self.nlines): yield self[i]

    def shapes(self):
        """Iterate through all the primitives contained in the set."""
        return self.lines()

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
