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

"""Contains objects representing controllers. Currently has partial
    support for loading Skin and Morph. **This module is highly
    experimental. More support will be added in version 0.4.**"""

import numpy

from collada import source
from collada.common import DaeObject, tag
from collada.common import DaeIncompleteError, DaeBrokenRefError, \
        DaeMalformedError, DaeUnsupportedError
from collada.geometry import Geometry
from collada.util import checkSource
from collada.xmlutil import etree as ElementTree
from collada import primitive

class Controller(DaeObject):
    """Base controller class holding data from <controller> tags."""

    def bind(self, matrix, materialnodebysymbol):
        pass

    @staticmethod
    def load( collada, localscope, node ):
        controller = node.find(tag('skin'))
        if controller is None:
            controller = node.find(tag('morph'))
        if controller is None: raise DaeUnsupportedError('Unknown controller node')

        sourcebyid = {}
        sources = []
        sourcenodes = node.findall('%s/%s'%(controller.tag, tag('source')))
        for sourcenode in sourcenodes:
            ch = source.Source.load(collada, {}, sourcenode)
            sources.append(ch)
            sourcebyid[ch.id] = ch

        if controller.tag == tag('skin'):
            return Skin.load(collada, sourcebyid, controller, node)
        else:
            return Morph.load(collada, sourcebyid, controller, node)

class BoundController( object ):
    """Base class for a controller bound to a transform matrix and materials mapping."""

class Skin(Controller):
    """Class containing data collada holds in the <skin> tag"""

    def __init__(self, bind_shape_matrix, joint_sources, weight_sources, weight_vcounts,
                    weight_indices, geometry, controller_node=None, skin_node=None):
        """Create a skin.

        :Parameters:
          bind_shape_matrix
            A numpy array of floats (pre-shape)
          joint_sources
            The list of joint source inputs for the vertex weights
          weight_sources
            The list of source inputs for the vertex weights
          weight_vcounts
            A list with the number of influences on each vertex
          weight_indices
            An array with the indexes as they come from <v> array
          geometry
            The source geometry this should be applied to (geometry.Geometry)
          controller_node
            XML node of the <controller> tag which is the parent of this
          skin_node
            XML node of the <skin> tag if this is from there

        """
        
        self.bind_shape_matrix = bind_shape_matrix
        """A 4x4 matrix in column-major order representing the position of the
        base mesh before binding"""
        self.weight_vcounts = weight_vcounts
        """Contains a numpy array of integers, each specifying the number of
        bones associated with one of the influences"""
        self.weight_indices = weight_indices
        """Contains a numpy array of integer indices that describe which bones
        and attributes are associated with each vertex. An index of -1 into
        the array of joints refers to the bind shape."""
        self.geometry = geometry
        """The geometry this skin references"""
        
        self.joint_sources = joint_sources
        self.weight_sources = weight_sources
        self.controller_node = controller_node
        self.skin_node = skin_node
        self.xmlnode = controller_node

        self.id = controller_node.get('id')
        """Unique identifier for the skin"""
        if self.id is None:
            raise DaeMalformedError('Controller node requires an ID')

        self.bind_shape_matrix.shape = (-1,)
        if len(bind_shape_matrix) != 16:
            raise DaeMalformedError('Invalid bind shape matrix input to Skin')
        self.bind_shape_matrix.shape = (4,4)
        
        if not isinstance(self.geometry, Geometry):
            raise DaeMalformedError('Invalid reference geometry in skin')

        if 'JOINT' not in self.joint_sources or \
                'INV_BIND_MATRIX' not in self.joint_sources or \
                len(self.joint_sources['JOINT']) != 1 or \
                len(self.joint_sources['INV_BIND_MATRIX']) != 1:
            raise DaeMalformedError('Invalid joint inputs in skin')
        
        self.joints = self.joint_sources['JOINT'][0][4].data.reshape(-1,)
        """A numpy array of length N joint names"""
        self.joint_weights = self.joint_sources['INV_BIND_MATRIX'][0][4].data
        """An Nx4x4 numpy array of joint matrices"""
        self.joint_weights.shape = (-1, 4, 4)
        if len(self.joints) != len(self.joint_weights):
            raise DaeMalformedError("Length of joint names and joint weights in skin don't match")

        #find max offset
        max_offset = max([max([input[0] for input in input_type_array])
                          for input_type_array in self.weight_sources.values() if len(input_type_array) > 0])
        self.nindices = max_offset + 1
        self.weight_indices.shape = (-1, self.nindices)
        self.weight_ends = numpy.cumsum(self.weight_vcounts)
        self.weight_starts = self.weight_ends - self.weight_vcounts
        
        # sum of the vcounts should equal length of reshaped indices
        if len(self.weight_indices) != self.weight_vcounts.sum():
            raise DaeMalformedError("Length of skin vertex weight indices does not match vcounts")
        
        # check to make sure joint and weight indices aren't out of range
        self.joint_offset = self.weight_sources['JOINT'][0][0]
        self.joint_source = self.weight_sources['JOINT'][0][4]
        self._joint_index = self.weight_indices[:, self.joint_offset]
        self.max_joint_index = self._joint_index.max()
        checkSource(self.joint_source, ('JOINT',), self.max_joint_index)
        self.weight_offset = self.weight_sources['WEIGHT'][0][0]
        self.weight_source = self.weight_sources['WEIGHT'][0][4]
        self._weight_index = self.weight_indices[:, self.weight_offset]
        self.max_weight_index = self._weight_index.max()
        checkSource(self.weight_source, ('WEIGHT',), self.max_weight_index)

    def __len__(self):
        return len(self.weight_vcounts)

    def bind(self, matrix, materialnodebysymbol):
        """Create a bound morph from this one, transform and material mapping"""
        return BoundSkin(self, matrix, materialnodebysymbol)

    @staticmethod
    def load( collada, localscope, skinnode, controllernode ):
        if len(localscope) < 3:
            raise DaeMalformedError('Not enough sources in skin')

        geometry_source = skinnode.get('source')
        if geometry_source is None or len(geometry_source) < 2 \
                or geometry_source[0] != '#':
            raise DaeBrokenRefError('Invalid source attribute of skin node')
        if not geometry_source[1:] in collada.geometries:
            raise DaeBrokenRefError('Source geometry for skin node not found')
        geometry = collada.geometries[geometry_source[1:]]

        bind_shape_mat = skinnode.find(tag('bind_shape_matrix'))
        if bind_shape_mat is None or bind_shape_mat.text is None:
            bind_shape_mat = numpy.identity(4, dtype=numpy.float32)
            bind_shape_mat.shape = (-1,)
        else:
            try:
                values = [float(v) for v in bind_shape_mat.text.split()]
            except ValueError:
                raise DaeMalformedError('Corrupted bind shape matrix in skin')
            bind_shape_mat = numpy.array( values, dtype=numpy.float32 )

        inputnodes = skinnode.findall('%s/%s' % (tag('joints'), tag('input')))
        if inputnodes is None or len(inputnodes) < 2:
            raise DaeIncompleteError("Not enough inputs in skin joints")
        joint_sources = primitive.Primitive._getInputs(collada, localscope, inputnodes)

        weightsnode = skinnode.find(tag('vertex_weights'))
        if weightsnode is None:
            raise DaeIncompleteError("No vertex_weights found in skin")
        indexnode = weightsnode.find(tag('v'))
        if indexnode is None or indexnode.text is None:
            raise DaeIncompleteError('Missing indices in skin vertex weights')
        vcountnode = weightsnode.find(tag('vcount'))
        if vcountnode is None or vcountnode.text is None:
            raise DaeIncompleteError('Missing vcount in skin vertex weights')
        
        try:
            weight_vcounts = numpy.fromstring(vcountnode.text, dtype=numpy.int32, sep=' ')
        except:
            raise DaeMalformedError('Corrupted vertex weight vcounts in skin')

        try:
            weight_indices = numpy.fromstring(indexnode.text, dtype=numpy.int32, sep=' ')
        except:
            raise DaeMalformedError('Corrupted vertex weight indices in skin')

        inputnodes = weightsnode.findall(tag('input'))
        weight_sources = primitive.Primitive._getInputs(collada, localscope, inputnodes)

        return Skin(bind_shape_mat, joint_sources, weight_sources, weight_vcounts,
                    weight_indices, geometry, controllernode, skinnode)

class BoundSkin(BoundController):
    """A skin bound to a transform matrix and materials mapping."""

    def __init__(self, skin, matrix, materialnodebysymbol):
        self.matrix = matrix
        self.materialnodebysymbol = materialnodebysymbol
        self.skin = skin
        self.id = skin.id
        self.index = skin.index
        self.joint_matrices = skin.joint_matrices
        self.geometry = skin.geometry.bind(numpy.dot(matrix,skin.bind_shape_matrix), materialnodebysymbol)

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        return self.index[i]

    def getJoint(self, i):
        return self.skin.weight_joints[i]

    def getWeight(self, i):
        return self.skin.weights[i]

    def primitives(self):
        for prim in self.geometry.primitives():
            bsp = BoundSkinPrimitive(prim, self)
            yield bsp


class BoundSkinPrimitive(object):
    """A bound skin bound to a primitive."""

    def __init__(self, primitive, boundskin):
        self.primitive = primitive
        self.boundskin = boundskin

    def __len__(self):
        return len(self.primitive)

    def shapes(self):
        for shape in self.primitive.shapes():
            indices = shape.indices
            yield shape


class Morph(Controller):
    """Class containing data collada holds in the <morph> tag"""

    def __init__(self, source_geometry, target_list, xmlnode=None):
        """Create a morph instance

        :Parameters:
          source_geometry
            The source geometry (Geometry)
          targets
            A list of tuples where each tuple (g,w) contains
            a Geometry (g) and a float weight value (w)
          xmlnode
            When loaded, the xmlnode it comes from

        """
        self.id = xmlnode.get('id')
        if self.id is None:
            raise DaeMalformedError('Controller node requires an ID')
        self.source_geometry = source_geometry
        """The source geometry (Geometry)"""
        self.target_list = target_list
        """A list of tuples where each tuple (g,w) contains
            a Geometry (g) and a float weight value (w)"""

        self.xmlnode = xmlnode
        #TODO

    def __len__(self):
        return len(self.target_list)

    def __getitem__(self, i):
        return self.target_list[i]

    def bind(self, matrix, materialnodebysymbol):
        """Create a bound morph from this one, transform and material mapping"""
        return BoundMorph(self, matrix, materialnodebysymbol)

    @staticmethod
    def load( collada, localscope, morphnode, controllernode ):
        baseid = morphnode.get('source')
        if len(baseid) < 2 or baseid[0] != '#' or \
                not baseid[1:] in collada.geometries:
            raise DaeBrokenRefError('Base source of morph %s not found' % baseid)
        basegeom = collada.geometries[baseid[1:]]

        method = morphnode.get('method')
        if method is None:
            method = 'NORMALIZED'
        if not (method == 'NORMALIZED' or method == 'RELATIVE'):
            raise DaeMalformedError("Morph method must be either NORMALIZED or RELATIVE. Found '%s'" % method)

        inputnodes = morphnode.findall('%s/%s'%(tag('targets'), tag('input')))
        if inputnodes is None or len(inputnodes) < 2:
            raise DaeIncompleteError("Not enough inputs in a morph")

        try:
            inputs = [(i.get('semantic'), i.get('source')) for i in inputnodes]
        except ValueError as ex:
            raise DaeMalformedError('Corrupted inputs in morph')

        target_source = None
        weight_source = None
        for i in inputs:
            if len(i[1]) < 2 or i[1][0] != '#' or not i[1][1:] in localscope:
                raise DaeBrokenRefError('Input in morph node %s not found' % i[1])
            if i[0] == 'MORPH_TARGET':
                target_source = localscope[i[1][1:]]
            elif i[0] == 'MORPH_WEIGHT':
                weight_source = localscope[i[1][1:]]

        if not type(target_source) is source.IDRefSource or \
                not type(weight_source) is source.FloatSource:
            raise DaeIncompleteError("Not enough inputs in targets of morph")

        if len(target_source) != len(weight_source):
            raise DaeMalformedError("Morph inputs must be of same length")

        target_list = []
        for target, weight in zip(target_source, weight_source):
            if len(target) < 1 or not(target in collada.geometries):
                raise DaeBrokenRefError("Targeted geometry %s in morph not found"%target)
            target_list.append((collada.geometries[target], weight[0]))

        return Morph(basegeom, target_list, controllernode)

    def save(self):
        #TODO
        pass


class BoundMorph(BoundController):
    """A morph bound to a transform matrix and materials mapping."""

    def __init__(self, morph, matrix, materialnodebysymbol):
        self.matrix = matrix
        self.materialnodebysymbol = materialnodebysymbol
        self.original = morph

    def __len__(self):
        return len(self.original)

    def __getitem__(self, i):
        return self.original[i]

