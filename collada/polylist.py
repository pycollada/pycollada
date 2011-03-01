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
from lxml import etree as ElementTree
import primitive
import types
import triangleset
from util import toUnitVec, checkSource
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, tag

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

class PolygonList(primitive.Primitive):
    """Class containing the data COLLADA puts in a <polylist> tag, a collection of faces."""

    def __init__(self, sources, material, index, vcounts, xmlnode=None):
        """Create a polygon list.

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

        self.nvertices = 0
        try:
            newshape = []
            at = 0
            for ct in self.vcounts:
                thispoly = self.index[self.nindices*at:self.nindices*(at+ct)]
                thispoly.shape = (ct, self.nindices)
                self.nvertices += ct
                newshape.append(numpy.array(thispoly))
                at+=ct
            self.index = newshape
        except:
            raise DaeMalformedError('Corrupted vcounts or index in polylist')

        self.npolygons = len(self.index)

        self._vertex = sources['VERTEX'][0][4].data
        self._vertex_index = [poly[:,sources['VERTEX'][0][0]] for poly in self.index]
        self.maxvertexindex = numpy.max( [numpy.max(poly) for poly in self._vertex_index] )
        checkSource(sources['VERTEX'][0][4], ('X', 'Y', 'Z'), self.maxvertexindex)

        if 'NORMAL' in sources and len(sources['NORMAL']) > 0:
            self._normal = sources['NORMAL'][0][4].data
            self._normal_index = [poly[:,sources['NORMAL'][0][0]] for poly in self.index]
            self.maxnormalindex = numpy.max( [numpy.max(poly) for poly in self._normal_index] )
            checkSource(sources['NORMAL'][0][4], ('X', 'Y', 'Z'), self.maxnormalindex)
        else:
            self._normal = None
            self._normal_index = None
            self.maxnormalindex = -1
            
        if 'TEXCOORD' in sources and len(sources['TEXCOORD']) > 0:
            self._texcoordset = tuple([texinput[4].data for texinput in sources['TEXCOORD']])
            self._texcoord_indexset = tuple([ [poly[:,sources['TEXCOORD'][i][0]] for poly in self.index]
                                             for i in xrange(len(sources['TEXCOORD'])) ])
            self.maxtexcoordsetindex = [ numpy.max([ numpy.max([p for p in poly])
                                        for poly in each ]) for each in self._texcoord_indexset ]
            for i, texinput in enumerate(sources['TEXCOORD']):
                checkSource(texinput[4], ('S', 'T'), self.maxtexcoordsetindex[i])
        else:
            self._texcoordset = tuple()
            self._texcoord_indexset = tuple()
            self.maxtexcoordsetindex = -1
            
        if xmlnode is not None: self.xmlnode = xmlnode
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

        all_inputs = primitive.Primitive.getInputs(localscope, node.findall(tag('input')))

        try:
            index = numpy.array([float(v) for v in indexnode.text.split()], dtype=numpy.int32)
        except: raise DaeMalformedError('Corrupted index in polylist')

        polylist = PolygonList(all_inputs, node.get('material'), index, vcounts)
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
        self.index = pl.index
        self.nvertices = pl.nvertices
        self._vertex_index = pl._vertex_index
        self._normal_index = pl._normal_index
        self._texcoord_indexset = pl._texcoord_indexset
        self.npolygons = pl.npolygons
        self.original = pl
    
    def __len__(self): return len(self.index)

    def __getitem__(self, i):
        v = self._vertex[ self._vertex_index[i] ]
        if self._normal is None:
            #don't general normals for polygons
            #let them get generated after triangulation
            n = None
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
