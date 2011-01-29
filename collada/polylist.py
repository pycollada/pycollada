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

"""Module containing classes and functions for the <polylist> primitive."""

import numpy
from xml.etree import ElementTree
import primitive
import types
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag

class Polygon(object):
    """Single polygon representation."""
    def __init__(self, indices, vertices, normals, texcoords, material):
        """Create a polygon from numpy arrays.

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
        """A (3, 3) float array with the normals por points a b c."""
        self.texcoords = texcoords
        """A tuple with (3, 2) float arrays with the texcoords."""
        self.material = material
        """Symbol (string) or the material object itself if bound."""

    def __repr__(self): 
        return 'Polygon (vertices=%d)' % len(self.vertices)
    def __str__(self): return repr(self)

class PolygonList(primitive.Primitive):
    """Class containing the data COLLADA puts in a <polylist> tag, a collection of faces."""

    def __init__(self, sourceById, vertex_source, normal_source, texcoord_sourceset, 
                 material, index, vcounts, xmlnode=None, stt={}, offsets=None):
        """Create a polygon list.

        :Parameters:
          sourceById 
            A dict mapping id's to a collada source
          vertex_source 
            The string id for the vertex source
          normal_source 
            The string id for the normal source
          texcoord_sourceset
            A tuple of strings with texcoord source ids
          material
            A string with the symbol of the material
          index
            An array with the indexes as they come from the collada file
          vcounts
            A list with the lengths of each individual polygon
          xmlnode
            An xml node in case this is loaded from there
          stt
            Ignored for now
          offsets
            A list with the offsets in the index array for each source
            in (vertex, normal, uv1, uv2, ...)

        """
        
        self.sourceById = sourceById
        self.texcoord_start = 1 if normal_source is None else 2
        if offsets: self.offsets = offsets
        else: self.offsets = range(self.texcoord_start + len(texcoord_sourceset))
        self.nindices = max(self.offsets) + 1
        self._vertex_source = vertex_source
        self._normal_source = normal_source
        self._texcoord_sourceset = tuple(texcoord_sourceset)
        try:
            self._vertex = self.sourceById[vertex_source].data
            if self._normal_source is None:
                self._normal = None
            else:
                self._normal = self.sourceById[normal_source].data
            self._texcoordset = tuple([ sourceById[c].data for c in texcoord_sourceset ])
        except KeyError, ex:
            raise DaeBrokenRefError('Referenced missing source in triangle set\n'+str(ex))
        self.material = material
        self.setToTexcoord = stt
        self.index = index
        self.vcounts = vcounts
        self.nsources = len(self._texcoord_sourceset) + (1 if self._normal is None else 2)

        try:
            newshape = []
            at = 0
            for ct in self.vcounts:
                thispoly = self.index[self.nindices*at:self.nindices*(at+ct)]
                thispoly.shape = (ct, self.nindices)
                newshape.append(numpy.array(thispoly))
                at+=ct
            self.index = newshape
        except:
            raise # DaeMalformedError('Corrupted vcounts or index in polylist')

        self._vertex_index = [poly[:, self.offsets[0]] for poly in self.index]
        if self._normal is None:
            self._normal_index = None
        else:
            self._normal_index = [poly[:, self.offsets[1]] for poly in self.index]
        self._texcoord_indexset = tuple( [[poly[:,self.offsets[self.texcoord_start+i]] for poly in self.index] 
                                         for i in xrange(len(self._texcoord_sourceset)) ])
        self.npolygons = len(self.index)
        self.maxvertexindex = numpy.max( [numpy.max(poly) for poly in self._vertex_index] )
        if self._normal is None:
            self.maxnormalindex = -1
        else:
            self.maxnormalindex = numpy.max( [numpy.max(poly) for poly in self._normal_index] )
        if len(self._texcoord_sourceset) == 0:
            self.maxtexcoordsetindex = -1
        else:
            self.maxtexcoordsetindex = [ numpy.max([ numpy.max([p for p in poly])
                        for poly in each ]) for each in self._texcoord_indexset ]
        checkSource(self.sourceById[self._vertex_source], ('X', 'Y', 'Z'), self.maxvertexindex)
        if not self._normal_source is None:
            checkSource(self.sourceById[self._normal_source], ('X', 'Y', 'Z'), self.maxnormalindex)
        for i, c in enumerate(self._texcoord_sourceset):
            checkSource(self.sourceById[c], ('S', 'T'), self.maxtexcoordsetindex[i])
        if xmlnode: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.fromstring("<polylist> <vcount></vcount> <p></p> </polylist>")

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
        except KeyError, ex: raise DaeBrokenRefError('Setting missing vertex source in polygon list')
        self._vertex_source = c
    
    def set_normal_source(self, c):
        try: self._normal = checkSource(self.sourceById[c],
                                         ('X', 'Y', 'Z'), self.maxnormalindex).data
        except KeyError, ex: raise DaeBrokenRefError('Setting missing normal source in polygon list')
        self._normal_source = c

    def set_texcoord_sourceset(self, t):
        if len(t) != len(self._texcoord_sourceset):
            raise DaeMalformedError('Wrong number of texcoord sources')
        try: self._texcoordset = tuple([ 
                    checkSource(self.sourceById[c], ('S', 'T'), 
                                 self.maxtexcoordsetindex[i]).data for i,c in enumerate(t)])
        except KeyError, ex: raise DaeBrokenRefError('Setting missing texcoord source in polygon list')
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
        return Polygon(self._vertex_index[i], v, n, uv, self.material)

    @staticmethod
    def load( collada, localscope, node ):
        indexnode = node.find(tag('p'))
        if indexnode is None: raise DaeIncompleteError('Missing index in polylist')
        vcountnode = node.find(tag('vcount'))
        if vcountnode is None: raise DaeIncompleteError('Missing vcount in polylist')

        try: 
            vcounts = numpy.array([float(v) for v in vcountnode.text.split()], dtype=numpy.int32)
        except ValueError, ex: raise DaeMalformedError('Corrupted vcounts in polylist')

        [vertex_i, has_normal, tex_start, index, inputs] = \
            primitive.Primitive.getInputs(localscope, indexnode, node.findall(tag('input')))

        if len(inputs) == 0: raise DaeIncompleteError('A polylist set needs at least one input for vertex positions')
        if inputs[0][1] != 'VERTEX': raise DaeMalformedError('First input in polylist set must be the vertex list')
        if len(inputs[0][2]) < 2 or inputs[0][2][0] != '#':
            raise DaeMalformedError('Incorrect source id in VERTEX input')
        
        if has_normal:
            if len(inputs[1][2]) < 2 or inputs[1][2][0] != '#':
                raise DaeMalformedError('Incorrect source id in NORMAL input')
            normal_source = inputs[1][2][1:]
        else:
            normal_source = None
            
        vertex_source = inputs[0][2][1:]
        texcoord_sourceset = []
        setToTexcoord = {}
        for offset, semantic, source, set in inputs[tex_start:]:
            if semantic != 'TEXCOORD': raise DaeUnsupportedError('Found unexpected input in polylist set: %s' % semantic)
            if set: setToTexcoord[set] = offset - tex_start
            if len(source) < 2 or source[0] != '#':
                raise DaeMalformedError('Incorrect source id in TEXCOORD input')
            texcoord_sourceset.append( source[1:] )
        polylist = PolygonList(localscope, vertex_source, normal_source, texcoord_sourceset, 
                             node.get('material'), index, vcounts, setToTexcoord,
                             offsets=[ t[0] for t in inputs])
        polylist.xmlnode = node
        return polylist

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
        """Create a bound polygon list from this polygon list, transform and material mapping"""
        return BoundPolygonList( self, matrix, materialnodebysymbol)

class BoundPolygonList(object):
    """A polygon set bound to a transform matrix and materials mapping."""

    def __init__(self, pl, matrix, materialnodebysymbol):
        """Create a bound polygon list from a polygon list, transform and material mapping"""
        M = numpy.asmatrix(matrix).transpose()
        self._vertex = numpy.asarray(pl._vertex * M[:3,:3]) + matrix[:3,3]
        self._normal = None if pl._normal is None else numpy.asarray(pl._normal * M[:3,:3])
        self._texcoordset = pl._texcoordset
        matnode = materialnodebysymbol.get( pl.material )
        if matnode:
            self.material = matnode.target
            self.inputmap = dict([ (sem, (input_sem, set)) for sem, input_sem, set in matnode.inputs ])
        else: self.inputmap = self.material = None
        self.setToTexcoord = pl.setToTexcoord
        self.index = pl.index
        self.nsources = pl.nsources
        self._vertex_index = pl._vertex_index
        self._normal_index = pl._normal_index
        self._texcoord_indexset = pl._texcoord_indexset
        self.npolygons = pl.npolygons
        self.original = pl
    
    def __len__(self): return len(self.index)

    def __getitem__(self, i):
        v = self._vertex[ self._vertex_index[i] ]
        if self._normal is None:
            #generate normals
            #TODO: is this correct?
            vec1 = numpy.subtract(v[0], v[1])
            vec2 = numpy.subtract(v[2], v[0])
            vec3 = toUnitVec(numpy.cross(toUnitVec(vec2), toUnitVec(vec1)))
            n = numpy.array([vec3, vec3, vec3])
        else:
            n = self._normal[ self._normal_index[i] ]
        uv = []
        for j, uvindex in enumerate(self._texcoord_indexset):
            uv.append( self._texcoordset[j][ uvindex[i] ] )
        return Polygon(self._vertex_index[i], v, n, uv, self.material)

    def polygons(self):
        """Iterate through all the polygons contained in the set."""
        for i in xrange(self.npolygons): yield self[i]

    def shapes(self):
        """Iterate through all the primitives contained in the set."""
        return self.polygons()

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
