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

"""Module for <geometry> data loading."""

from xml.etree import ElementTree
import numpy
import source
import triangleset
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag

def cleanId( text ):
    if text and text[0] == '#': return text[1:]
    else: return text

class Geometry( DaeObject ):
    """A class containing the data coming from a COLLADA <geometry> tag"""

    # TODO: poner el id como argumento
    def __init__(self, sources, sourcebyid, vertexsource, primitives, xmlnode=None):
        """Create a geometry instance

        :Parameters:
          sources
            A list of data sources (source.Source)
          sourcebyid
            A dictionary mapping source ids to the actual objects
          vertexsource
            A string selecting one of the sources as vertex source 
          primitives
            List of primitive objects contained
          xmlnode
            When loaded, the xmlnode it comes from

        """
        self.sources = sources
        """Source list inside this geometry tag."""
        self.sourceById = sourcebyid
        """Sources indexed by id."""
        self.vertexsource = vertexsource
        """The source id used as vertex list."""
        self._primitives = primitives
        if xmlnode != None: 
            self.xmlnode = xmlnode
            self.id = xmlnode.get('id')
        else:
            self.id = gid or 'geometry' + str(id(self))
            self.xmlnode = ElementTree.Element('geometry')
            mesh = ElementTree.Element('mesh')
            self.xmlnode.append( mesh )
            for source in sources:
                mesh.append( source.xmlnode )
            vxml = ''
            for semantic, source in self.sourceById[self.vertexsource].items():
                vxml.append('<input semantic="%s" source="#%s" />' % (semantic, source.id))
            vxml = '<vertices id="%s">%s</vertices>' % (self.vertexsource, vxml)
            mesh.append( ElementTree.fromstring(vxml) )
            for tset in _primitives:
                mesh.append(tset.xmlnode)

    primitives = property( lambda s: tuple(s._primitives) )
    """Primitive object list inside this geometry."""

    @staticmethod
    def load( collada, localscope, node ):
        meshnode = node.find(tag('mesh'))
        if meshnode is None: raise DaeUnsupportedError('Unknown geometry node')
        sourcebyid = {}
        sources = []
        sourcenodes = node.findall('%s/%s'%(tag('mesh'), tag('source')))
        for sourcenode in sourcenodes:
            ch = source.Source.load(collada, {}, sourcenode)
            sources.append(ch)
            sourcebyid[ch.id] = ch
        _primitives = []
        vertexsource = None
        for subnode in meshnode:
            if subnode.tag == tag('vertices'):
                inputnodes = {}
                for inputnode in subnode.findall(tag('input')):
                    semantic = inputnode.get('semantic')
                    inputsource = inputnode.get('source')
                    if not semantic or not inputsource or not inputsource.startswith('#'):
                        raise DaeIncompleteError('Bad input definition inside vertices')
                    inputnodes[semantic] = sourcebyid.get(inputsource[1:])
                if (not subnode.get('id') or len(inputnodes)==0 or 
                    not 'POSITION' in inputnodes):
                    raise DaeIncompleteError('Bad vertices definition in mesh')
                sourcebyid[subnode.get('id')] = inputnodes
                vertexsource = subnode.get('id')
            elif subnode.tag == tag('triangles'):
                _primitives.append( triangleset.TriangleSet.load( collada, sourcebyid, subnode ) )
            elif subnode.tag != tag('source'):
                raise DaeUnsupportedError('Unknown geometry tag %s' % subnode.tag)
        geom = Geometry( sources, sourcebyid, vertexsource, _primitives, xmlnode=node )
        return geom

    def save(self):
        #TODO: Update this with new sourceById format
        for ch in self.sources: ch.save()
        vnode = self.xmlnode.find(tag('mesh')).find(tag('vertices'))
        vinput = vnode.find(tag('input'))
        vnode.set('id', self.vertexsource)
        vinput.set('source', '#'+self.sourceById[self.vertexsource].id)
        for t in self._primitives: t.save()
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)

    def bind(self, matrix, materialnodebysymbol):
        """Create a bound geometry from this one, transform and material mapping"""
        return BoundGeometry(self, matrix, materialnodebysymbol)

class BoundGeometry( object ):
    """A geometry bound to a transform matrix and materials mapping."""

    def __init__(self, geom, matrix, materialnodebysymbol):
        """Create a bound geometry from a geometry, transform and material mapping"""
        self.matrix = matrix
        self.materialnodebysymbol = materialnodebysymbol
        self._primitives = geom._primitives
        self.original = geom

    def __len__(self): return len(self._primitives)

    def primitives(self):
        """Iterate through all the primitives inside the geometry."""
        for p in self._primitives:
            boundp = p.bind( self.matrix, self.materialnodebysymbol )
            yield boundp
