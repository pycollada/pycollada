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

"""This module contains several classes related to the scene graph.

Supported scene nodes are:
  * <node> which is loaded as a Node
  * <instance_camera> which is loaded as a CameraNode
  * <instance_light> which is loaded as a LightNode
  * <instance_material> which is loaded as a MaterialNode
  * <instance_geometry> which is loaded as a GeometryNode
  * <instance_controller> which is loaded as a ControllerNode
  * <scene> which is loaded as a Scene

"""

import copy
import numpy

from .common import DaeObject, E, tag, get_number_dtype
from .common import DaeError, DaeIncompleteError, DaeBrokenRefError, \
        DaeMalformedError, DaeUnsupportedError
from .util import toUnitVec
from .xmlutil import etree as ElementTree
from .extra import Extra
from .transform import Transform, TranslateTransform, RotateTransform, ScaleTransform, MatrixTransform, LookAtTransform

class DaeInstanceNotLoadedError(Exception):
    """Raised when an instance_node refers to a node that isn't loaded yet. Will always be caught"""
    def __init__(self, msg):
        super(DaeInstanceNotLoadedError,self).__init__()
        self.msg = msg


class SceneNode(DaeObject):
    """Abstract base class for all nodes within a scene."""

    def objects(self, tipo, matrix=None):
        """Iterate through all objects under this node that match `tipo`.
        The objects will be bound and transformed via the scene transformations.

        :param str tipo:
          A string for the desired object type. This can be one of 'geometry',
          'camera', 'light', or 'controller'.
        :param numpy.matrix matrix:
          An optional transformation matrix

        :rtype: generator that yields the type specified

        """
        pass


class Node(SceneNode):
    """Represents a node object, which is a point on the scene graph, as defined in the collada <node> tag.

    Contains the list of transformations effecting the node as well as any children.
    """

    def __init__(self, id, sid=None, name=None, type=None, layer=None, children=None, transforms=None, extras=None, xmlnode=None):
        """Create a node in the scene graph.

        :param str id:
          A unique string identifier for the node
        :param list children:
          A list of child nodes of this node. This can contain any
          object that inherits from :class:`collada.scene.SceneNode`
        :param list transforms:
          A list of transformations effecting the node. This can
          contain any object that inherits from :class:`collada.transform.Transform`
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.id = id
        self.sid = sid
        self.name = name
        self.type = type
        self.layer = layer
        """The unique string identifier for the node"""
        self.children = []
        """A list of child nodes of this node. This can contain any
          object that inherits from :class:`collada.scene.SceneNode`"""
        if children is not None:
            self.children = children
        self.transforms = []
        if transforms is not None:
            self.transforms = transforms
        """A list of transformations effecting the node. This can
          contain any object that inherits from :class:`collada.transform.Transform`"""
        self.matrix = numpy.identity(4, dtype=get_number_dtype())
        """A numpy.array of size 4x4 containing a transformation matrix that
        combines all the transformations in :attr:`transforms`. This will only
        be updated after calling :meth:`save`."""
        self.extras = []
        if extras is not None:
            self.extras = extras

        for t in self.transforms:
            self.matrix = numpy.dot(self.matrix, t.matrix)

        if xmlnode is not None:
            self.xmlnode = xmlnode
            """ElementTree representation of the transform."""
        else:
            self.xmlnode = E.node(id=self.id, name=self.id)
            self.save(0)

    def objects(self, tipo, matrix=None):
        """Iterate through all objects under this node that match `tipo`.
        The objects will be bound and transformed via the scene transformations.

        :param str tipo:
          A string for the desired object type. This can be one of 'geometry',
          'camera', 'light', or 'controller'.
        :param numpy.matrix matrix:
          An optional transformation matrix

        :rtype: generator that yields the type specified

        """
        if matrix != None: M = numpy.dot( matrix, self.matrix )
        else: M = self.matrix
        for node in self.children:
            for obj in node.objects(tipo, M):
                yield obj

    def save(self,recurse=True):
        """Saves the geometry back to :attr:`xmlnode`. Also updates
        :attr:`matrix` if :attr:`transforms` has been modified."""
        Extra.saveextras(self.xmlnode,self.extras)
        self.matrix = numpy.identity(4, dtype=get_number_dtype())
        for t in self.transforms:
            self.matrix = numpy.dot(self.matrix, t.matrix)

        if recurse:
            for child in self.children:
                child.save(recurse)
                
        if self.id is not None:
            self.xmlnode.set('id', self.id)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
        if self.type is not None:
            self.xmlnode.set('type',self.type)
        else:
            self.xmlnode.attrib.pop('type',None)
        if self.layer is not None:
            self.xmlnode.set('layer',self.layer)
        else:
            self.xmlnode.attrib.pop('layer',None)
        for t in self.transforms:
            if recurse:
                t.save(recurse)
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
    def load( collada, node, localscope ):
        id = node.get('id')
        sid = node.get('sid')
        name = node.get('name')
        type = node.get('type')
        layer = node.get('layer')
        children = []
        transforms = []

        for subnode in node:
            try:
                n = loadNode(collada, subnode, localscope)
                if isinstance(n, Transform):
                    transforms.append(n)
                elif n is not None:
                    children.append(n)
            except DaeError as ex:
                collada.handleError(ex)

        extras = Extra.loadextras(collada, node)
        return Node(id, sid, name, type, layer, children, transforms, extras, xmlnode=node)

    def __str__(self):
        return '<Node transforms=%d, children=%d>' % (len(self.transforms), len(self.children))

    def __repr__(self):
        return str(self)


class NodeNode(Node):
    """Represents a node being instantiated in a scene, as defined in the collada <instande_node> tag."""

    def __init__(self, node, sid=None, name=None, url=None, proxy=None, extras=None, xmlnode=None):
        """Creates a node node

        :param collada.scene.Node node:
          A node to instantiate in the scene, can be None to indicate that the url was not resolved
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.node = node
        """An object of type :class:`collada.scene.Node` representing the node to bind in the scene"""
        self.sid=sid
        self.name=name
        self.url=url
        self.proxy=proxy
        self.extras = []
        if extras is not None:
            self.extras = extras
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the node node."""
        else:
            self.xmlnode = E.instance_node()
            self.save(0)

    def objects(self, tipo, matrix=None):
        for obj in self.node.objects(tipo, matrix):
            yield obj

    id = property(lambda s: s.node.id)
    children = property(lambda s: s.node.children)
    matrix = property(lambda s: s.node.matrix)

    @staticmethod
    def load( collada, node, localscope ):
        referred_node=None
        sid = node.get("sid")
        name = node.get("name")
        url = node.get('url')
        proxy = node.get('proxy')
        if url.startswith('#'):
            referred_node = localscope.get(url[1:])
            if not referred_node:
                referred_node = collada.nodes.get(url[1:])
        extras = Extra.loadextras(collada, node)
        return NodeNode(referred_node, sid, name, url, proxy, extras, xmlnode=node)

    def save(self, recurse=True):
        """Saves the node node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.node is not None:
            self.xmlnode.set('url', "#%s" % self.node.id)
        else:
            self.xmlnode.set('url',self.url)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
        if self.proxy is not None:
            self.xmlnode.set('proxy',self.proxy)
        else:
            self.xmlnode.attrib.pop('proxy',None)

    def __str__(self):
        return '<NodeNode node=%s>' % (self.node.id,)

    def __repr__(self):
        return str(self)


class GeometryNode(SceneNode):
    """Represents a geometry instance in a scene, as defined in the collada <instance_geometry> tag."""

    def __init__(self, geometry, materials=None, extras=None, xmlnode=None):
        """Creates a geometry node

        :param collada.geometry.Geometry geometry:
          A geometry to instantiate in the scene
        :param list materials:
          A list containing items of type :class:`collada.scene.MaterialNode`.
          Each of these represents a material that the geometry should be
          bound to.
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.geometry = geometry
        """An object of type :class:`collada.geometry.Geometry` representing the
        geometry to bind in the scene"""
        self.materials = []
        """A list containing items of type :class:`collada.scene.MaterialNode`.
          Each of these represents a material that the geometry is bound to."""
        if materials is not None:
            self.materials = materials
        self.extras = []
        if extras is not None:
            self.extras = extras
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry node."""
        else:
            self.xmlnode = E.instance_geometry(url="#%s" % self.geometry.id)
            if len(self.materials) > 0:
                self.xmlnode.append(E.bind_material(
                    E.technique_common(
                        *[mat.xmlnode for mat in self.materials]
                    )
                ))

    def objects(self, tipo, matrix=None):
        """Yields a :class:`collada.geometry.BoundGeometry` if ``tipo=='geometry'``"""
        if tipo == 'geometry':
            if matrix is None: matrix = numpy.identity(4, dtype=get_number_dtype())
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
        extras = Extra.loadextras(collada, node)
        return GeometryNode( geometry, materials, extras, xmlnode=node)

    def save(self, recurse=True):
        """Saves the geometry node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('url', "#%s" % self.geometry.id)

        if recurse:
            for m in self.materials:
                m.save(recurse)

        matparent = self.xmlnode.find('%s/%s'%( tag('bind_material'), tag('technique_common') ) )
        if matparent is None and len(self.materials)==0:
            return
        elif matparent is None:
            matparent = E.technique_common()
            self.xmlnode.append(E.bind_material(matparent))
        elif len(self.materials) == 0 and matparent is not None:
            bindnode = self.xmlnode.find('%s' % tag('bind_material'))
            self.xmlnode.remove(bindnode)
            return

        for m in self.materials:
            if m.xmlnode not in matparent:
                matparent.append(m.xmlnode)
        xmlnodes = [m.xmlnode for m in self.materials]
        for n in matparent:
            if n not in xmlnodes:
                matparent.remove(n)

    def __str__(self):
        return '<GeometryNode geometry=%s>' % (self.geometry.id,)

    def __repr__(self):
        return str(self)


class ControllerNode(SceneNode):
    """Represents a controller instance in a scene, as defined in the collada <instance_controller> tag. **This class is highly
    experimental. More support will be added in version 0.4.**"""

    def __init__(self, controller, materials, extras=None, xmlnode=None):
        """Creates a controller node

        :param collada.controller.Controller controller:
          A controller to instantiate in the scene
        :param list materials:
          A list containing items of type :class:`collada.scene.MaterialNode`.
          Each of these represents a material that the controller should be
          bound to.
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.controller = controller
        """ An object of type :class:`collada.controller.Controller` representing
        the controller being instantiated in the scene"""
        self.materials = materials
        """A list containing items of type :class:`collada.scene.MaterialNode`.
          Each of these represents a material that the controller is bound to."""
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the controller node."""
        else:
            self.xmlnode = ElementTree.Element( tag('instance_controller') )
            bindnode = ElementTree.Element( tag('bind_material') )
            technode = ElementTree.Element( tag('technique_common') )
            bindnode.append( technode )
            self.xmlnode.append( bindnode )
            for mat in materials: technode.append( mat.xmlnode )

    def objects(self, tipo, matrix=None):
        """Yields a :class:`collada.controller.BoundController` if ``tipo=='controller'``"""
        if tipo == 'controller':
            if matrix is None: matrix = numpy.identity(4, dtype=get_number_dtype())
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
        extras = Extra.loadextras(collada, node)
        return ControllerNode( controller, materials, xmlnode=node)

    def save(self, recurse=True):
        """Saves the controller node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('url', '#'+self.controller.id)
        if recurse:
            for mat in self.materials:
                mat.save()

    def __str__(self):
        return '<ControllerNode controller=%s>' % (self.controller.id,)

    def __repr__(self):
        return str(self)


class MaterialNode(SceneNode):
    """Represents a material being instantiated in a scene, as defined in the collada <instance_material> tag."""

    def __init__(self, symbol, target, inputs, extras=None, xmlnode = None):
        """Creates a material node

        :param str symbol:
          The symbol within a geometry this material should be bound to
        :param collada.material.Material target:
          The material object being bound to
        :param list inputs:
          A list of tuples of the form ``(semantic, input_semantic, set)`` mapping
          texcoords or other inputs to material input channels, e.g.
          ``('TEX0', 'TEXCOORD', '0')`` would map the effect parameter ``'TEX0'``
          to the ``'TEXCOORD'`` semantic of the geometry, using texture coordinate
          set ``0``.
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.symbol = symbol
        """The symbol within a geometry this material should be bound to"""
        self.target = target
        """An object of type :class:`collada.material.Material` representing the material object being bound to"""
        self.inputs = inputs
        """A list of tuples of the form ``(semantic, input_semantic, set)`` mapping
          texcoords or other inputs to material input channels, e.g.
          ``('TEX0', 'TEXCOORD', '0')`` would map the effect parameter ``'TEX0'``
          to the ``'TEXCOORD'`` semantic of the geometry, using texture coordinate
          set ``0``."""
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode is not None:
            self.xmlnode = xmlnode
            """ElementTree representation of the material node."""
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
        extras = Extra.loadextras(collada, node)
        return MaterialNode(node.get('symbol'), target, inputs, extras, xmlnode = node)

    def objects(self):
        pass

    def save(self, recurse=True):
        """Saves the material node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('symbol', self.symbol)
        self.xmlnode.set('target', "#%s"%self.target.id)

        inputs_in = []
        for i in self.xmlnode.findall( tag('bind_vertex_input') ):
            input_tuple = ( i.get('semantic'), i.get('input_semantic'), i.get('input_set') )
            if input_tuple not in self.inputs:
                self.xmlnode.remove(i)
            else:
                inputs_in.append(input_tuple)
        for i in self.inputs:
            if i not in inputs_in:
                self.xmlnode.append(E.bind_vertex_input(semantic=i[0], input_semantic=i[1], input_set=i[2]))

    def __str__(self):
        return '<MaterialNode symbol=%s targetid=%s>' % (self.symbol, self.target.id)

    def __repr__(self):
        return str(self)


class CameraNode(SceneNode):
    """Represents a camera being instantiated in a scene, as defined in the collada <instance_camera> tag."""

    def __init__(self, camera, extras=None, xmlnode=None):
        """Create a camera instance

        :param collada.camera.Camera camera:
          The camera being instantiated
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.camera = camera
        """An object of type :class:`collada.camera.Camera` representing the instantiated camera"""
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the camera node."""
        else:
            self.xmlnode = E.instance_camera(url="#%s"%camera.id)

    def objects(self, tipo, matrix=None):
        """Yields a :class:`collada.camera.BoundCamera` if ``tipo=='camera'``"""
        if tipo == 'camera':
            if matrix is None: matrix = numpy.identity(4, dtype=get_number_dtype())
            yield self.camera.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in camera instance %s' % url)
        camera = collada.cameras.get(url[1:])
        if not camera: raise DaeBrokenRefError('Camera %s not found in library'%url)
        extras = Extra.loadextras(collada, node)
        return CameraNode( camera, extras, xmlnode=node)

    def save(self,recurse=True):
        """Saves the camera node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('url', '#'+self.camera.id)

    def __str__(self):
        return '<CameraNode camera=%s>' % (self.camera.id,)

    def __repr__(self):
        return str(self)


class LightNode(SceneNode):
    """Represents a light being instantiated in a scene, as defined in the collada <instance_light> tag."""

    def __init__(self, light, extras=None, xmlnode=None):
        """Create a light instance

        :param collada.light.Light light:
          The light being instantiated
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.light = light
        """An object of type :class:`collada.light.Light` representing the instantiated light"""
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the light node."""
        else:
            self.xmlnode = E.instance_light(url="#%s"%light.id)

    def objects(self, tipo, matrix=None):
        """Yields a :class:`collada.light.BoundLight` if ``tipo=='light'``"""
        if tipo == 'light':
            if matrix is None: matrix = numpy.identity(4, dtype=get_number_dtype())
            yield self.light.bind(matrix)

    @staticmethod
    def load( collada, node ):
        url = node.get('url')
        if not url.startswith('#'): raise DaeMalformedError('Invalid url in light instance %s' % url)
        light = collada.lights.get(url[1:])
        if not light: raise DaeBrokenRefError('Light %s not found in library'%url)
        extras = Extra.loadextras(collada, node)
        return LightNode( light, extras, xmlnode=node)

    def save(self,recurse=True):
        """Saves the light node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('url', '#'+self.light.id)

    def __str__(self): return '<LightNode light=%s>' % (self.light.id,)
    def __repr__(self): return str(self)

def loadNode( collada, node, localscope ):
    """Generic scene node loading from a xml `node` and a `collada` object.

    Knowing the supported nodes, create the appropiate class for the given node
    and return it.

    """
    if node.tag == tag('node'): return Node.load(collada, node, localscope)
    elif node.tag == tag('translate'): return TranslateTransform.load(collada, node)
    elif node.tag == tag('rotate'): return RotateTransform.load(collada, node)
    elif node.tag == tag('scale'): return ScaleTransform.load(collada, node)
    elif node.tag == tag('matrix'): return MatrixTransform.load(collada, node)
    elif node.tag == tag('lookat'): return LookAtTransform.load(collada, node)
    elif node.tag == tag('instance_geometry'): return GeometryNode.load(collada, node)
    elif node.tag == tag('instance_camera'): return CameraNode.load(collada, node)
    elif node.tag == tag('instance_light'): return LightNode.load(collada, node)
    elif node.tag == tag('instance_controller'): return ControllerNode.load(collada, node)
    elif node.tag == tag('instance_node'): return NodeNode.load(collada, node, localscope)
    elif node.tag == tag('extra'):
        return Extra.load(collada, localscope, node)
    elif node.tag == tag('asset'):
        return None
    else: raise DaeUnsupportedError('Unknown scene node %s' % str(node.tag))


class Scene(DaeObject):
    """The root object for a scene, as defined in a collada <scene> tag"""

    def __init__(self, id, nodes, extras=None, xmlnode=None, collada=None):
        """Create a scene

        :param str id:
          A unique string identifier for the scene
        :param list nodes:
          A list of type :class:`collada.scene.Node` representing the nodes in the scene
        :param xmlnode:
          When loaded, the xmlnode it comes from
        :param collada:
          The collada instance this is part of

        """
        self.id = id
        """The unique string identifier for the scene"""
        self.nodes = nodes
        """A list of type :class:`collada.scene.Node` representing the nodes in the scene"""
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the scene node."""
        else:
            self.xmlnode = E.visual_scene(id=self.id)
            for node in nodes:
                self.xmlnode.append( node.xmlnode )

    def objects(self, tipo):
        """Iterate through all objects in the scene that match `tipo`.
        The objects will be bound and transformed via the scene transformations.

        :param str tipo:
          A string for the desired object type. This can be one of 'geometry',
          'camera', 'light', or 'controller'.

        :rtype: generator that yields the type specified

        """
        matrix = None
        for node in self.nodes:
            for obj in node.objects(tipo, matrix): yield obj

    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        nodes = []
        tried_loading = []
        succeeded = False
        localscope = {}
        for nodenode in node.findall(tag('node')):
            try:
                N = loadNode(collada, nodenode, localscope)
            except DaeInstanceNotLoadedError as ex:
                tried_loading.append((nodenode, ex))
            except DaeError as ex:
                collada.handleError(ex)
            else:
                if N is not None:
                    nodes.append( N )
                    if N.id and N.id not in localscope:
                        localscope[N.id] = N
                    succeeded = True
        while len(tried_loading) > 0 and succeeded:
            succeeded = False
            next_tried = []
            for nodenode, ex in tried_loading:
                try:
                    N = loadNode(collada, nodenode, localscope)
                except DaeInstanceNotLoadedError as ex:
                    next_tried.append((nodenode, ex))
                except DaeError as ex:
                    collada.handleError(ex)
                else:
                    if N is not None:
                        nodes.append( N )
                        succeeded = True
            tried_loading = next_tried
        if len(tried_loading) > 0:
            for nodenode, ex in tried_loading:
                raise DaeBrokenRefError(ex.msg)
        extras = Extra.loadextras(collada, node)
        return Scene(id, nodes, extras, xmlnode=node, collada=collada)

    def save(self,recurse=True):
        """Saves the scene back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('id', self.id)
        for node in self.nodes:
            if recurse:
                node.save(recurse)
            if node.xmlnode not in self.xmlnode:
                self.xmlnode.append(node.xmlnode)
        xmlnodes = [n.xmlnode for n in self.nodes]
        for node in self.xmlnode:
            if node not in xmlnodes:
                self.xmlnode.remove(node)

    def __str__(self):
        return '<Scene id=%s nodes=%d>' % (self.id, len(self.nodes))

    def __repr__(self):
        return str(self)

