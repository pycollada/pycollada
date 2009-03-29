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

"""This module contains several classes to load nodes under <scene> tag.

Supported scene nodes are:
- <node> which is treated as a TransformNode
- <instance_camera> which is treated as CameraNode
- <instance_material> which is treated as MaterialNode
- <instance_geometry> which is treated as GeometryNode
- <scene> created as Scene class instance containing all the rest

"""

from xml.etree import ElementTree
import numpy
from collada import DaeObject, DaeError, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag

def cleanId( text ):
    if text and text[0] == '#': return text[1:]
    else: return text

class SceneNode(DaeObject):
    """Base class for all <scene> stuff."""

    def objects(self, tipo, matrix=None): 
        """Iterate through all objects under this node that match `tipo`

        All objects are yielded transformed where they need to.

        :Parameters:
          tipo
            A string for the desired object type ('geometry' or 'camera')
          matrix
            An optional transform matrix

        """
        pass

def makeRotationMatrix(x, y, z, angle):
    """Build and return a transform 4x4 matrix to rotate `angle` radians 
    around (`x`,`y`,`z`) axis."""
    c = numpy.cos(angle)
    s = numpy.sin(angle)
    t = (1-c)
    return numpy.array([[t*x*x+c,     t*x*y - s*z, t*x*z + s*y, 0],
                        [t*x*y+s*z,   t*y*y + c,   t*y*z - s*x, 0],
                        [t*x*z - s*y, t*y*z + s*x, t*z*z + c,   0],
                        [0,           0,           0,           1]],
                       dtype=numpy.float32 )

class TransformNode(SceneNode):
    """Class containing data from <node> tags

    Since all node tags can contain transform directives we treat
    all of them as TransformNode, even if the transform is the
    identity.

    """

    def __init__(self, id, matrix, nodes, xmlnode=None):
        """Create a TransformNode.

        :Parameters:
          id
            Id inside scene
          matrix
            A 4x4 numpy array with the transform matrix
          nodes
            child node list
          xmlnode
            If loaded from XML, the xml node it comes from

        """
        self.id = id
        """Id inside scene."""
        self.matrix = matrix
        """Numpy transform matrix."""
        self.nodes = nodes
        """child node list."""
        if xmlnode: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element(tag('node'))
            for node in nodes:
                self.xmlnode.append( node.xmlnode )
   
    def objects(self, tipo, matrix=None):
        if matrix != None: M = numpy.dot( matrix, self.matrix )
        else: M = self.matrix
        for node in self.nodes:
            for obj in node.objects(tipo, M):
                yield obj

    def save(self):
        if not (self.matrix == numpy.identity(4)).all():
            mnode = self.xmlnode.find('matrix')
            if mnode is None:
                mnode = ElementTree.Element(tag('matrix'))
                self.xmlnode.insert(0, mnode)
            mnode.text = str(numpy.reshape(self.matrix, (-1,)))[1:-1]
        else:
            mnode = self.xmlnode.find('matrix')
            if mnode != None: self.xmlnode.remove(mnode)
        for n in self.nodes: n.save()

    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        matrices = [ numpy.identity(4) ]
        nodes = []
        toremove = []
        try:
            for tnode in node:
                if tnode.tag == tag('translate'):
                    m = numpy.identity(4)
                    m[:3,3] = [ float(x) for x in tnode.text.split()]
                    matrices.append(m)
                    toremove.append(tnode)
                elif tnode.tag == tag('rotate'):
                    vx, vy, vz, angle = [ float(x) for x in tnode.text.split()]
                    matrices.append( makeRotationMatrix(vx, vy, vz, angle*numpy.pi/180.0) )
                    toremove.append(tnode)
                elif tnode.tag == tag('scale'):
                    m = numpy.identity(4)
                    t = [ float(x) for x in tnode.text.split()]
                    for i in xrange(3): m[i,i] = t[i]
                    matrices.append(m)
                    toremove.append(tnode)
                elif tnode.tag == tag('matrix'):
                    m = numpy.array([ float(x) for x in tnode.text.split()], dtype=numpy.float32)
                    if len(m) != 16: raise DaeMalformedError('Corrupted transformation node')
                    m.shape = (4, 4)
                    matrices.append(m)
                    toremove.append(tnode)
        except ValueError, ex: raise DaeMalformedError('Corrupted transformation node')
        while len(matrices) > 1:
            matrices = matrices[:-2] + [ numpy.dot(matrices[-2], matrices[-1]) ]
        for n in toremove: node.remove(n)
        for nodenode in node:
            try: nodes.append( loadNode(collada, nodenode) )
            except DaeError, ex: collada.handleError(ex)
        return TransformNode(id, matrices[0], nodes, xmlnode=node)

class GeometryNode(SceneNode):
    """Data coming from <instance_geometry> inside the scene tree."""

    def __init__(self, geometry, materials, xmlnode=None):
        """Create a GeometryNode.

        :Parameters:
          geometry
            A `Geometry` instance from geometry library
          materials
            A list of `MaterialNode` objects inside this node
          xmlnode
            If loaded from XML, the node it comes from

        """
        self.geometry = geometry
        """A `Geometry` instance from geometry library."""
        self.materials = materials
        """A list of `MaterialNode` objects inside this node."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('instance_geometry') )
            bindnode = ElementTree.Element( tag('bind_material') )
            technode = ElementTree.Element( tag('technique_common') )
            bindnode.append( technode )
            self.xmlnode.append( bindnode )
            for mat in materials: technode.append( mat.xmlnode )
            
    def objects(self, tipo, matrix=None):
        if tipo == 'geometry':
            if matrix is None: matrix = numpy.identity(4)
            materialnodesbysymbol = {}
            for mat in self.materials:
                materialnodesbysymbol[mat.symbol] = mat
            yield self.geometry.bind(matrix, materialnodesbysymbol)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in geometry instance')
        geometry = collada.geometryById.get(url[1:])
        if not geometry: raise DaeBrokenRefError('Geometry %s not found in library'%url)
        matnodes = node.findall('%s/%s/%s'%( tag('bind_material'), tag('technique_common'), tag('instance_material') ) )
        materials = []
        for matnode in matnodes:
            materials.append( MaterialNode.load(collada, matnode) )
        return GeometryNode( geometry, materials, xmlnode=node)

    def save(self):
        self.xmlnode.set('url', '#'+self.geometry.id)
        for mat in self.materials: mat.save()

class MaterialNode(SceneNode):
    """Data coming from <instance_material> inside <instance_geometry> in scene tree."""

    def __init__(self, symbol, target, inputs, xmlnode = None):
        """Create a MaterialNode.

        :Parameters:
          symbol
            The symbol string (inside the geometry object) we are defining
          target
            The id of the material to assign to the symbol
          inputs
            A list of tuples (semantic, input_semantic, set) mapping geometry
            texcoords or other inputs to material input channels (semantic)
          xmlnode
            If loaded from XML, the node it comes from

        """
        self.symbol = symbol
        """The symbol string (inside the geometry object) we are defining."""
        self.target = target
        """The id of the material to assign to the symbol."""
        self.inputs = inputs
        """A list of tuples (semantic, input_semantic, set) mapping material inputs."""
        if xmlnode: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('instance_material') )
            self.xmlnode.set('symbol', symbol)
            self.xmlnode.set('target', '#' + target.id)
            for sem, input_sem, set in inputs:
                inputnode = ElementTree.ElementTree( tag('bind_vertex_input') )
                inputnode.set('semantic', sem)
                inputnode.set('input_semantic', input_sem)
                inputnode.set('input_set', set)
                self.xmlnode.append( inputnode )

    def findInput(self, semantic):
        """Return the xml node assigning something to `semantic`."""
        for node in self.xmlnode.findall(tag('bind_vertex_input')):
            if node.get('semantic') == semantic: return node
        node = ElementTree.Element(tag('bind_vertex_input'))
        node.set('semantic', semantic)
        self.xmlnode.append( node )
        return node

    def save(self):
        self.xmlnode.set( 'symbol', self.symbol )
        self.xmlnode.set( 'target', '#'+self.target.id )
        for sem, input_sem, set in self.inputs:
            inputnode = self.findInput(sem)
            inputnode.set('input_semantic', input_sem)
            inputnode.set('input_set', set)
            
    @staticmethod
    def load(collada, node):
        inputs = []
        for inputnode in node.findall( tag('bind_vertex_input') ):
            inputs.append( ( inputnode.get('semantic'), inputnode.get('input_semantic'), inputnode.get('input_set') ) )
        targetid = node.get('target')
        if not targetid.startswith('#'): raise DaeMalformedError('Incorrect target id in material '+targetid)
        target = collada.materialById.get(targetid[1:])
        if not target: raise DaeBrokenRefError('Material %s not found'%targetid)
        return MaterialNode(node.get('symbol'), target, inputs, xmlnode = node)

class CameraNode(SceneNode):
    """Camera binding inside of scene tree as <instance_camera> tag."""

    def __init__(self, camera, xmlnode=None):
        """Create a CameraNode out of a `camera` from the library."""
        self.camera = camera
        """Original camera from the library."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('instance_camera') )
            self.xmlnode.set('url', '#'+camera.id)
            
    def objects(self, tipo, matrix=None):
        if tipo == 'camera':
            if matrix is None: matrix = numpy.identity(4)
            yield self.camera.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in camera instance')
        camera = collada.cameraById.get(url[1:])
        if not camera: raise DaeBrokenRefError('Camera %s not found in library'%url)
        return CameraNode( camera, xmlnode=node)

    def save(self):
        self.xmlnode.set('url', '#'+self.camera.id)

class LightNode(SceneNode):
    """Light binding inside of scene tree as <instance_light> tag."""

    def __init__(self, light, xmlnode=None):
        """Create a LightNode out of a `light` from the library."""
        self.light = light
        """Original camera from the library."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('instance_light') )
            self.xmlnode.set('url', '#'+light.id)
            
    def objects(self, tipo, matrix=None):
        if tipo == 'light':
            if matrix is None: matrix = numpy.identity(4)
            yield self.light.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in light instance')
        light = collada.lightById.get(url[1:])
        if not light: raise DaeBrokenRefError('Light %s not found in library'%url)
        return LightNode( light, xmlnode=node)

    def save(self):
        self.xmlnode.set('url', '#'+self.light.id)

def loadNode( collada, node ):
    """Generic scene node loading from a xml `node` and a `collada` object.

    Knowing the supported nodes, create the appropiate class for the given node
    and return it.

    """
    if node.tag == tag('node'): return TransformNode.load(collada, node)
    elif node.tag == tag('instance_geometry'): return GeometryNode.load(collada, node)
    elif node.tag == tag('instance_camera'): return CameraNode.load(collada, node)
    elif node.tag == tag('instance_light'): return LightNode.load(collada, node)
    else: raise DaeUnsupportedError('Unknown scene node '+node.tag)

class Scene(DaeObject):
    """Scene data (a tree) for <scene> tag and children."""
    
    def __init__(self, id, nodes, xmlnode=None):
        """Create a Scene node from a children list (`nodes`) of `SceneNode`."""
        self.id = id
        """Id inside scene library."""
        self.nodes = nodes
        """Children node list."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element(tag('visual_scene'))
            for node in nodes:
                self.xmlnode.append( node.xmlnode )

    def objects(self, tipo):
        """Iterate through all objects under this node that match `tipo`

        All objects are yielded transformed where they need to.

        :Parameters:
          tipo
            A string for the desired object type ('geometry' or 'camera')

        """
        for node in self.nodes:
            for obj in node.objects(tipo): yield obj

    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        nodes = []
        for nodenode in node.findall( tag('node') ):
            try: nodes.append( loadNode(collada, nodenode) )
            except DaeError, ex: collada.handleError(ex)
        return Scene(id, nodes, xmlnode=node)

    def save(self):
        self.xmlnode.set('id', self.id)
        for node in self.nodes:
            node.save()

