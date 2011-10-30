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

"""Module containing the base class for primitives"""
import numpy
import types

from collada.common import DaeObject
from collada.common import DaeIncompleteError, DaeBrokenRefError, \
        DaeMalformedError, DaeUnsupportedError
from collada.source import InputList

class Primitive(DaeObject):
    """Base class for all primitive sets like TriangleSet, LineSet, Polylist, etc."""

    vertex = property( lambda s: s._vertex, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertex points in the
    primitive's vertex source array.""" )
    normal = property( lambda s: s._normal, doc=
    """Read-only numpy.array of size Nx3 where N is the number of normal values in the
    primitive's normal source array.""" )
    texcoordset = property( lambda s: s._texcoordset, doc=
    """Read-only tuple of texture coordinate arrays. Each value is a numpy.array of size
    Nx2 where N is the number of texture coordinates in the primitive's source array.""" )
    textangentset = property( lambda s: s._textangentset, doc=
    """Read-only tuple of texture tangent arrays. Each value is a numpy.array of size
    Nx3 where N is the number of texture tangents in the primitive's source array.""" )
    texbinormalset = property( lambda s: s._texbinormalset, doc=
    """Read-only tuple of texture binormal arrays. Each value is a numpy.array of size
    Nx3 where N is the number of texture binormals in the primitive's source array.""" )

    vertex_index = property( lambda s: s._vertex_index, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertices in the primitive.
    To get the actual vertex points, one can use this array to select into the vertex
    array, e.g. ``vertex[vertex_index]``.""" )
    normal_index = property( lambda s: s._normal_index, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertices in the primitive.
    To get the actual normal values, one can use this array to select into the normals
    array, e.g. ``normal[normal_index]``.""" )
    texcoord_indexset = property( lambda s: s._texcoord_indexset, doc=
    """Read-only tuple of texture coordinate index arrays. Each value is a numpy.array of size
    Nx2 where N is the number of vertices in the primitive. To get the actual texture
    coordinates, one can use the array to select into the texcoordset array, e.g.
    ``texcoordset[0][texcoord_indexset[0]]`` would select the first set of texture
    coordinates.""" )
    textangent_indexset = property( lambda s: s._textangent_indexset, doc=
    """Read-only tuple of texture tangent index arrays. Each value is a numpy.array of size
    Nx3 where N is the number of vertices in the primitive. To get the actual texture
    tangents, one can use the array to select into the textangentset array, e.g.
    ``textangentset[0][textangent_indexset[0]]`` would select the first set of texture
    tangents.""" )
    texbinormal_indexset = property( lambda s: s._texbinormal_indexset, doc=
    """Read-only tuple of texture binormal index arrays. Each value is a numpy.array of size
    Nx3 where N is the number of vertices in the primitive. To get the actual texture
    binormals, one can use the array to select into the texbinormalset array, e.g.
    ``texbinormalset[0][texbinormal_indexset[0]]`` would select the first set of texture
    binormals.""" )

    def bind(self, matrix, materialnodebysymbol):
        """Binds this primitive to a transform matrix and material mapping.
        The primitive's points get transformed by the given matrix and its
        inputs get mapped to the given materials.

        :param numpy.array matrix:
          A 4x4 numpy float matrix
        :param dict materialnodebysymbol:
          A dictionary with the material symbols inside the primitive
          assigned to :class:`collada.scene.MaterialNode` defined in the
          scene

        :rtype: :class:`collada.primitive.Primitive`

        """
        pass

    @staticmethod
    def _getInputsFromList(collada, localscope, inputs):
        #first let's save any of the source that are references to a dict
        to_append = []
        for input in inputs:
            offset, semantic, source, set = input
            if semantic == 'VERTEX':
                vertex_source = localscope.get(source[1:])
                if isinstance(vertex_source, dict):
                    for inputsemantic, inputsource in vertex_source.items():
                        if inputsemantic == 'POSITION':
                            to_append.append([offset, 'VERTEX', '#' + inputsource.id, set])
                        else:
                            to_append.append([offset, inputsemantic, '#' + inputsource.id, set])

        #remove all the dicts
        inputs[:] = [input for input in inputs
                if not isinstance(localscope.get(input[2][1:]), dict)]

        #append the dereferenced dicts
        for a in to_append:
            inputs.append(a)

        vertex_inputs = []
        normal_inputs = []
        texcoord_inputs = []
        textangent_inputs = []
        texbinormal_inputs = []
        color_inputs = []
        tangent_inputs = []
        binormal_inputs = []

        all_inputs = {}

        for input in inputs:
            offset, semantic, source, set = input
            if len(source) < 2 or source[0] != '#':
                raise DaeMalformedError('Incorrect source id "%s" in input' % source)
            if source[1:] not in localscope:
                raise DaeBrokenRefError('Source input id "%s" not found' % source)
            input = (input[0], input[1], input[2], input[3], localscope[source[1:]])
            if semantic == 'VERTEX':
                vertex_inputs.append(input)
            elif semantic == 'NORMAL':
                normal_inputs.append(input)
            elif semantic == 'TEXCOORD':
                texcoord_inputs.append(input)
            elif semantic == 'TEXTANGENT':
                textangent_inputs.append(input)
            elif semantic == 'TEXBINORMAL':
                texbinormal_inputs.append(input)
            elif semantic == 'COLOR':
                color_inputs.append(input)
            elif semantic == 'TANGENT':
                tangent_inputs.append(input)
            elif semantic == 'BINORMAL':
                binormal_inputs.append(input)
            else:
                try:
                    raise DaeUnsupportedError('Unknown input semantic: %s' % semantic)
                except DaeUnsupportedError as ex:
                    collada.handleError(ex)
                unknown_input = all_inputs.get(semantic, [])
                unknown_input.append(input)
                all_inputs[semantic] = unknown_input

        all_inputs['VERTEX'] = vertex_inputs
        all_inputs['NORMAL'] = normal_inputs
        all_inputs['TEXCOORD'] = texcoord_inputs
        all_inputs['TEXBINORMAL'] = texbinormal_inputs
        all_inputs['TEXTANGENT'] = textangent_inputs
        all_inputs['COLOR'] = color_inputs
        all_inputs['TANGENT'] = tangent_inputs
        all_inputs['BINORMAL'] = binormal_inputs

        return all_inputs

    @staticmethod
    def _getInputs(collada, localscope, inputnodes):
        try:
            inputs = [(int(i.get('offset')), i.get('semantic'),
                    i.get('source'), i.get('set'))
                for i in inputnodes]
        except ValueError as ex:
            raise DaeMalformedError('Corrupted offsets in primitive')

        return Primitive._getInputsFromList(collada, localscope, inputs)

    def getInputList(self):
        """Gets a :class:`collada.source.InputList` representing the inputs from a primitive"""
        inpl = InputList()
        for (key, tupes) in self.sources.iteritems():
            for (offset, semantic, source, set, srcobj) in tupes:
                inpl.addInput(offset, semantic, source, set)
        return inpl

    def save(self):
        return NotImplementedError("Primitives are read-only")

class BoundPrimitive(object):
    """A :class:`collada.primitive.Primitive` bound to a transform matrix
    and material mapping."""

    def shapes(self):
        """Iterate through the items in this primitive. The shape returned
        depends on the primitive type. Examples: Triangle, Polygon."""
        pass

    vertex = property( lambda s: s._vertex, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertex points in the
    primitive's vertex source array. The values will be transformed according to the
    bound transformation matrix.""" )
    normal = property( lambda s: s._normal, doc=
    """Read-only numpy.array of size Nx3 where N is the number of normal values in the
    primitive's normal source array. The values will be transformed according to the
    bound transformation matrix.""" )
    texcoordset = property( lambda s: s._texcoordset, doc=
    """Read-only tuple of texture coordinate arrays. Each value is a numpy.array of size
    Nx2 where N is the number of texture coordinates in the primitive's source array. The
    values will be transformed according to the bound transformation matrix.""" )
    vertex_index = property( lambda s: s._vertex_index, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertices in the primitive.
    To get the actual vertex points, one can use this array to select into the vertex
    array, e.g. ``vertex[vertex_index]``. The values will be transformed according to the
    bound transformation matrix.""" )
    normal_index = property( lambda s: s._normal_index, doc=
    """Read-only numpy.array of size Nx3 where N is the number of vertices in the primitive.
    To get the actual normal values, one can use this array to select into the normals
    array, e.g. ``normal[normal_index]``. The values will be transformed according to the
    bound transformation matrix.""" )
    texcoord_indexset = property( lambda s: s._texcoord_indexset, doc=
    """Read-only tuple of texture coordinate index arrays. Each value is a numpy.array of size
    Nx2 where N is the number of vertices in the primitive. To get the actual texture
    coordinates, one can use the array to select into the texcoordset array, e.g.
    ``texcoordset[0][texcoord_indexset[0]]`` would select the first set of texture
    coordinates. The values will be transformed according to the bound transformation matrix.""" )
