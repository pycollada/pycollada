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

if __name__ == '__main__':
    import re
    xmlfromblender = """
        <geometry id="Plane_001-Geometry" name="Plane_001-Geometry">
            <mesh>
                <source id="Plane_001-Geometry-Position">
                    <float_array count="12" id="Plane_001-Geometry-Position-array">1.0 1.0 0.0 1.0 -1.0 0.0 -1.0 -1.0 0.0 -1.0 1.0 0.0</float_array>
                    <technique_common>
                        <accessor count="4" source="#Plane_001-Geometry-Position-array" stride="3">
                            <param name="X" type="float" />
                            <param name="Y" type="float" />
                            <param name="Z" type="float" />
                        </accessor>
                    </technique_common>
                </source>
                <source id="Plane_001-Geometry-Normals">
                    <float_array count="3" id="Plane_001-Geometry-Normals-array">0.0 -0.0 1.0</float_array>
                    <technique_common>
                        <accessor count="1" source="#Plane_001-Geometry-Normals-array" stride="3">
                            <param name="X" type="float" />
                            <param name="Y" type="float" />
                            <param name="Z" type="float" />
                        </accessor>
                    </technique_common>
                </source>
                <vertices count="4" id="Plane_001-Geometry-Vertex">
                    <input semantic="POSITION" source="#Plane_001-Geometry-Position" />
                </vertices>
                <triangles count="2" material="luzmat">
                    <input offset="0" semantic="VERTEX" source="#Plane_001-Geometry-Vertex" />
                    <input offset="1" semantic="NORMAL" source="#Plane_001-Geometry-Normals" />
                    <p>0 0 3 0 2 0 2 0 1 0 0 0</p>
                </triangles>
            </mesh>
        </geometry>
        """

    def checkXmlFragment(xmlfrag):
        geometryElement = ElementTree.fromstring(xmlfrag)
        xmlfrag = ElementTree.tostring( geometryElement )
        geom = Geometry.load( geometryElement )
        oldtlen = len(geom._primitives[0])
        assert oldtlen > 0
        assert type(geom._primitives[0][-1].vertices[0][0]) == numpy.float32
        geom.save()
        out = ElementTree.tostring(geom.xmlnode)
        xmlfrag = re.sub(r'[ \t\n]+', ' ', xmlfrag).strip()
        out = re.sub(r'[ \t\n]+', ' ', out).strip()
        assert out == xmlfrag
        geom = Geometry.load( ElementTree.fromstring(out) )
        assert len(geom._primitives[0]) == oldtlen
        geom._primitives[0].vertex[:,0] = 3.5
        assert geom._primitives[0][-1].vertices[0][0] == 3.5
        geom.save()
        out = ElementTree.tostring(geom.xmlnode)
        geom = Geometry.load( ElementTree.fromstring(out) )
        assert geom._primitives[0][-1].vertices[0][0] == 3.5

    channels = [
        channel.Source( numpy.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], 
                                     dtype=numpy.float32), ('X', 'Y', 'Z'), 'vertex-source-position' ),
        channel.Source( numpy.array([[0, 0, 1], [0, 0, 1]], 
                                     dtype=numpy.float32), ('X', 'Y', 'Z'), 'normal-source' ),
        channel.Source( numpy.array([[0, 0], [1, 0], [1, 1], [0, 1]],
                                     dtype=numpy.float32), ('S', 'T'), 'uv1-source' ),
        channel.Source( numpy.array([[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]],
                                     dtype=numpy.float32), ('S', 'T'), 'uv2-source' ) ]
    channelbyid = { 'vertex-source-position':channels[0],
                    'vertex-source':channels[0],
                    'normal-source':channels[1],
                    'uv1-source':channels[2],
                    'uv2-source':channels[3] }
    
    index = numpy.array( [ 0, 0, 0,  1, 0, 1,   2, 0, 2,
                           2, 1, 2,  3, 1, 3,   0, 1, 0 ], dtype=numpy.int32 )
    triset = _primitives.TriangleSet(channelbyid, 'vertex-source', 'normal-source', ['uv1-source'], 
                         'mat', index)
    geometry = Geometry( channels, channelbyid, 'vertex-source', [triset] )
    assert geometry._primitives[0].texcoordset[0][1][0] == 1.0
    triset.texcoord_channelset = ['uv2-source']
    assert geometry._primitives[0].texcoordset[0][1][0] == 0.5
    checkXmlFragment(xmlfromblender)
    print 'Blender xml passed'
    #checkXmlFragment(xmlfromskup)
    #print 'Sketchup xml passed'
    print 'All tests passed OK'
