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

"""This module contains several classes to load nodes under <scene> tag.

Supported scene nodes are:
- <node> which is treated as a Node
- <instance_camera> which is treated as CameraNode
- <instance_material> which is treated as MaterialNode
- <instance_geometry> which is treated as GeometryNode
- <scene> created as Scene class instance containing all the rest

"""

from lxml import etree as ElementTree
import numpy
from util import toUnitVec
from collada import DaeObject, DaeError, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag, E
import copy

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

class Transform(DaeObject):
    """Base class for all transformation types"""

class TranslateTransform(Transform):
    def __init__(self, x, y, z, xmlnode=None):
        self.x = x
        self.y = y
        self.z = z
        self.matrix = numpy.identity(4, dtype=numpy.float32)
        self.matrix[:3,3] = [ x, y, z ]
        self.xmlnode = xmlnode
        if xmlnode is None:
            self.xmlnode = E.translate(' '.join([str(x),str(y),str(z)]))
    @staticmethod
    def load(collada, node):
        floats = numpy.fromstring(node.text, dtype=numpy.float32, sep=' ')
        if len(floats) != 3:
            raise DaeMalformedError("Transform node requires three float values")
        return TranslateTransform(floats[0], floats[1], floats[2], node)
    
class RotateTransform(Transform):
    def __init__(self, x, y, z, angle, xmlnode=None):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.matrix = makeRotationMatrix(x, y, z, angle*numpy.pi/180.0)
        self.xmlnode = xmlnode
        if xmlnode is None:
            self.xmlnode = E.rotate(' '.join([str(x),str(y),str(z),str(angle)]))
    @staticmethod
    def load(collada, node):
        floats = numpy.fromstring(node.text, dtype=numpy.float32, sep=' ')
        if len(floats) != 4:
            raise DaeMalformedError("Rotate node requires four float values")
        return RotateTransform(floats[0], floats[1], floats[2], floats[3], node)
    
class ScaleTransform(Transform):
    def __init__(self, x, y, z, xmlnode=None):
        self.x = x
        self.y = y
        self.z = z
        self.matrix = numpy.identity(4, dtype=numpy.float32)
        self.matrix[0,0] = x
        self.matrix[1,1] = y
        self.matrix[2,2] = z
        self.xmlnode = xmlnode
        if xmlnode is None:
            self.xmlnode = E.scale(' '.join([str(x),str(y),str(z)]))
    @staticmethod
    def load(collada, node):
        floats = numpy.fromstring(node.text, dtype=numpy.float32, sep=' ')
        if len(floats) != 3:
            raise DaeMalformedError("Scale node requires three float values")
        return ScaleTransform(floats[0], floats[1], floats[2], node)
    
class MatrixTransform(Transform):
    def __init__(self, matrix, xmlnode=None):
        self.matrix = matrix
        if len(self.matrix) != 16: raise DaeMalformedError('Corrupted matrix transformation node')
        self.matrix.shape = (4, 4)
        self.xmlnode = xmlnode
        if xmlnode is None:
            self.xmlnode = E.matrix(' '.join([str(v) for v in self.matrix.flat]))
    @staticmethod
    def load(collada, node):
        floats = numpy.fromstring(node.text, dtype=numpy.float32, sep=' ')
        return MatrixTransform(floats, node)

class LookAtTransform(Transform):
    def __init__(self, eye, interest, upvector, xmlnode=None):
        self.eye = eye
        self.interest = interest
        self.upvector = upvector

        if len(eye) != 3 or len(interest) != 3 or len(upvector) != 3:
            raise DaeMalformedError('Corrupted lookat transformation node')
        
        self.matrix = numpy.identity(4, dtype=numpy.float32)

        front = toUnitVec(numpy.subtract(eye,interest))
        side = numpy.multiply(-1, toUnitVec(numpy.cross(front, upvector)))
        self.matrix[0,0:3] = side
        self.matrix[1,0:3] = upvector
        self.matrix[2,0:3] = front
        self.matrix[3,0:3] = eye

        self.xmlnode = xmlnode
        if xmlnode is None:
            self.xmlnode = E.lookat(' '.join([str(f) for f in 
                                        numpy.concatenate((self.eye, self.interest, self.upvector)) ]))
    @staticmethod
    def load(collada, node):
        floats = numpy.fromstring(node.text, dtype=numpy.float32, sep=' ')
        if len(floats) != 9:
            raise DaeMalformedError("Lookat node requires 9 float values")
        return LookAtTransform(floats[0:3], floats[3:6], floats[6:9], node)

class Node(SceneNode):
    """Class containing data from <node> tags

    Since all node tags can contain transform directives we treat
    all of them as Node, even if the transform is the
    identity.

    """

    def __init__(self, id, children=[], transforms=[], xmlnode=None):
        """Create a Node.

        :Parameters:
          id
            Id inside scene
          children
            A list of child nodes of this node
          transforms
            A list of transformations of type Transform
          xmlnode
            If loaded from XML, the xml node it comes from

        """
        self.id = id
        """Id inside scene."""
        self.transforms = transforms
        """A list of transformations of type Transform"""
        self.children = children
        """A list of child nodes of this node"""
        self.matrix = numpy.identity(4, dtype=numpy.float32)
        """numpy transformation matrix that combines all transform matrices"""

        for t in transforms:
            self.matrix = numpy.dot(self.matrix, t.matrix)

        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            self.xmlnode = E.node(id=self.id, name=self.id)
            for t in self.transforms:
                self.xmlnode.append(t.xmlnode)
            for c in self.children:
                self.xmlnode.append(c.xmlnode)
   
    def objects(self, tipo, matrix=None):
        if matrix != None: M = numpy.dot( matrix, self.matrix )
        else: M = self.matrix
        for node in self.children:
            for obj in node.objects(tipo, M):
                yield obj

    def save(self):
        self.matrix = numpy.identity(4, dtype=numpy.float32)
        for t in self.transforms:
            self.matrix = numpy.dot(self.matrix, t.matrix)
        
        for child in self.children:
            child.save()
            
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        for t in self.transforms:
            if t.xmlnode not in self.xmlnode:
                self.xmlnode.append(t.xmlnode)
        for c in self.children:
            if c.xmlnode not in self.xmlnode:
                self.xmlnode.append(c.xmlnode)
        xmlnodes = [c.xmlnode for c in self.children]
        xmlnodes.extend([t.xmlnode for t in self.transforms])
        for n in self.xmlnode:
            if n not in xmlnodes:
                self.xmlnode.remove(n)

    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        children = []
        transforms = []

        for subnode in node:
            try:
                n = loadNode(collada, subnode)
                if isinstance(n, Transform):
                    transforms.append(n)
                elif n is not None:
                    children.append(n)
            except DaeError, ex: collada.handleError(ex)

        return Node(id, children, transforms, xmlnode=node)

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
            self.xmlnode = E.instance_geometry(
                E.bind_material(
                    E.technique_common(
                        *[mat.xmlnode for mat in self.materials]
                    )
                )
            , url="#%s" % self.geometry.id)
            
    def objects(self, tipo, matrix=None):
        if tipo == 'geometry':
            if matrix is None: matrix = numpy.identity(4, dtype=numpy.float32)
            materialnodesbysymbol = {}
            for mat in self.materials:
                materialnodesbysymbol[mat.symbol] = mat
            yield self.geometry.bind(matrix, materialnodesbysymbol)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in geometry instance %s' % url)
        geometry = collada.geometries.get(url[1:])
        if not geometry: raise DaeBrokenRefError('Geometry %s not found in library'%url)
        matnodes = node.findall('%s/%s/%s'%( tag('bind_material'), tag('technique_common'), tag('instance_material') ) )
        materials = []
        for matnode in matnodes:
            materials.append( MaterialNode.load(collada, matnode) )
        return GeometryNode( geometry, materials, xmlnode=node)

class ControllerNode(SceneNode):
    """Data coming from <instance_controller> inside the scene tree."""

    def __init__(self, controller, materials, xmlnode=None):
        """Create a ControllerNode.

        :Parameters:
          controller
            A `Controller` instance from controller library
          materials
            A list of `MaterialNode` objects inside this node
          xmlnode
            If loaded from XML, the node it comes from

        """
        self.controller = controller
        """A `Controller` instance from controller library."""
        self.materials = materials
        """A list of `MaterialNode` objects inside this node."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('instance_controller') )
            bindnode = ElementTree.Element( tag('bind_material') )
            technode = ElementTree.Element( tag('technique_common') )
            bindnode.append( technode )
            self.xmlnode.append( bindnode )
            for mat in materials: technode.append( mat.xmlnode )
            
    def objects(self, tipo, matrix=None):
        if tipo == 'controller':
            if matrix is None: matrix = numpy.identity(4, dtype=numpy.float32)
            materialnodesbysymbol = {}
            for mat in self.materials:
                materialnodesbysymbol[mat.symbol] = mat
            yield self.controller.bind(matrix, materialnodesbysymbol)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in controller instance %s' % url)
        controller = collada.controllers.get(url[1:])
        if not controller: raise DaeBrokenRefError('Controller %s not found in library'%url)
        matnodes = node.findall('%s/%s/%s'%( tag('bind_material'), tag('technique_common'), tag('instance_material') ) )
        materials = []
        for matnode in matnodes:
            materials.append( MaterialNode.load(collada, matnode) )
        return ControllerNode( controller, materials, xmlnode=node)

    def save(self):
        self.xmlnode.set('url', '#'+self.controller.id)
        for mat in self.materials: mat.save()
        
class MaterialNode(SceneNode):
    """Data coming from <instance_material> inside <instance_geometry> in scene tree."""

    def __init__(self, symbol, target, inputs, xmlnode = None):
        """Create a MaterialNode.

        :Parameters:
          symbol
            The symbol string (inside the geometry object) we are defining
          target
            The material.Material object this refers to
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
        if xmlnode is not None: self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_material(
                *[E.bind_vertex_input(semantic=sem, input_semantic=input_sem, input_set=set)
                  for sem, input_sem, set in self.inputs]
            , **{'symbol': self.symbol, 'target':"#%s"%self.target.id} )
            
    @staticmethod
    def load(collada, node):
        inputs = []
        for inputnode in node.findall( tag('bind_vertex_input') ):
            inputs.append( ( inputnode.get('semantic'), inputnode.get('input_semantic'), inputnode.get('input_set') ) )
        targetid = node.get('target')
        if not targetid.startswith('#'): raise DaeMalformedError('Incorrect target id in material '+targetid)
        target = collada.materials.get(targetid[1:])
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
            self.xmlnode = E.instance_camera(url="#%s"%camera.id)
            
    def objects(self, tipo, matrix=None):
        if tipo == 'camera':
            if matrix is None: matrix = numpy.identity(4, dtype=numpy.float32)
            yield self.camera.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in camera instance %s' % url)
        camera = collada.cameras.get(url[1:])
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
            self.xmlnode = E.instance_light(url="#%s"%light.id)
            
    def objects(self, tipo, matrix=None):
        if tipo == 'light':
            if matrix is None: matrix = numpy.identity(4, dtype=numpy.float32)
            yield self.light.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in light instance %s' % url)
        light = collada.lights.get(url[1:])
        if not light: raise DaeBrokenRefError('Light %s not found in library'%url)
        return LightNode( light, xmlnode=node)

    def save(self):
        self.xmlnode.set('url', '#'+self.light.id)

class ExtraNode(SceneNode):
    """Stores an <extra> tag."""

    def __init__(self, xmlnode):
        """Create an ExtraNode which stores arbitrary xml."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = E.extra()
            
    def objects(self, tipo, matrix=None):
        if tipo == 'extra':
            for e in self.xmlnode.findall(tag(tipo)):
                yield e

    @staticmethod
    def load( collada, node ):
        return ExtraNode(node)

    def save(self):
        pass

def loadNode( collada, node ):
    """Generic scene node loading from a xml `node` and a `collada` object.

    Knowing the supported nodes, create the appropiate class for the given node
    and return it.

    """
    if node.tag == tag('node'): return Node.load(collada, node)
    elif node.tag == tag('translate'): return TranslateTransform.load(collada, node)
    elif node.tag == tag('rotate'): return RotateTransform.load(collada, node)
    elif node.tag == tag('scale'): return ScaleTransform.load(collada, node)
    elif node.tag == tag('matrix'): return MatrixTransform.load(collada, node)
    elif node.tag == tag('lookat'): return LookAtTransform.load(collada, node)
    elif node.tag == tag('instance_geometry'): return GeometryNode.load(collada, node)
    elif node.tag == tag('instance_camera'): return CameraNode.load(collada, node)
    elif node.tag == tag('instance_light'): return LightNode.load(collada, node)
    elif node.tag == tag('instance_controller'): return ControllerNode.load(collada, node)
    elif node.tag == tag('instance_node'):
        url = node.get('url')
        if not url.startswith('#'):
            raise DaeMalformedError('Invalid url in camera instance %s' % url)
        referred_node = collada.nodes.get(url[1:])
        if not referred_node:
            raise DaeBrokenRefError('Node %s not found in library'%url)
        return referred_node
    elif node.tag == tag('extra'):
        return ExtraNode.load(collada, node)
    elif node.tag == tag('asset'):
        return None
    else: raise DaeUnsupportedError('Unknown scene node %s' % str(node.tag))

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
            self.xmlnode = E.visual_scene(id=self.id)
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
        
        realnode = node
        if collada.assetInfo['up_axis'] == 'X_UP' or collada.assetInfo['up_axis'] == 'Y_UP':
            newscene = ElementTree.Element(tag('visual_scene'), {'id':'pycolladavisualscene', 'name':'pycolladavisualscene'})
            extranode = ElementTree.SubElement(newscene, tag('node'), {'id':'pycolladarotate', 'name':'pycolladarotate'})
            rotatenode = ElementTree.SubElement(extranode, tag('rotate'), {'sid':'rotateX'})
            rotatenode.text = "1 0 0 90" if collada.assetInfo['up_axis'] == 'Y_UP' else "0 1 0 90"
            
            prev_elements = list(node)
            for e in prev_elements:
                extranode.append(copy.deepcopy(e))
                
            realnode = newscene
        
        for nodenode in realnode.findall( tag('node') ):
            try: nodes.append( loadNode(collada, nodenode) )
            except DaeError, ex: collada.handleError(ex)
        return Scene(id, nodes, xmlnode=node)

    def save(self):
        self.xmlnode.set('id', self.id)
        for node in self.nodes:
            node.save()
            if node.xmlnode not in self.xmlnode:
                self.xmlnode.append(node.xmlnode)
        xmlnodes = [n.xmlnode for n in self.nodes]
        for node in self.xmlnode:
            if node not in xmlnodes:
                self.xmlnode.remove(node)
