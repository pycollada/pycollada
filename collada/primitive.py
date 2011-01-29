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

"""Module containing the base class for primitives"""
from collada import DaeObject
import numpy
import types

class Primitive(DaeObject):
    """Base class for all primitive sets like triangle sets."""

    def bind(self, matrix, materialnodebysymbol):
        """Create a copy of the primitive under the given transform.

        Creates a copy of the primitive with its points transformed
        by the given matrix and with material symbols set according
        to the given mapping

        :Parameters:
          matrix
            A 4x4 numpy float matrix
          materialnodebysymbol
            a dictionary with the material symbols inside the object 
            assigned to MaterialNodes defined in the scene

        """
        pass

    @staticmethod
    def getInputs(localscope, indexnode, inputnodes):
        try: 
            index = numpy.array([float(v) for v in indexnode.text.split()], dtype=numpy.int32)
            inputs = [ (int(i.get('offset')), i.get('semantic'), i.get('source'), i.get('set')) 
                           for i in inputnodes ]
        except ValueError, ex: raise DaeMalformedError('Corrupted index or offsets in polylist')
        
        vertex_i = -1
        for i in range(0,len(inputs)):
            if inputs[i][1] == 'VERTEX':
                vertex_i = i
        if vertex_i != -1:
            offset, semantic, source, set = inputs[vertex_i]
            vertex_source = localscope.get(source[1:])
            if type(vertex_source) == types.DictType:
                for inputsemantic, inputsource in vertex_source.items():
                    if inputsemantic == 'POSITION':
                        inputs[vertex_i] = [inputs[vertex_i][0], 'VERTEX', '#' + inputsource.id, inputs[vertex_i][3]]
                    else:
                        inputs.append([offset, inputsemantic, '#' + inputsource.id, set])
        
        inputs.sort()
        
        #make sure vertex is first and normal is second
        vertex_i = -1
        for i in range(0,len(inputs)):
            if inputs[i][1] == 'VERTEX':
                vertex_i = i
        if vertex_i != -1 and vertex_i != 0:
            inputs.insert(0, inputs.pop(vertex_i))
        normal_i = -1
        for i in range(0,len(inputs)):
            if inputs[i][1] == 'NORMAL':
                normal_i = i
        if normal_i != -1 and normal_i != 1:
            inputs.insert(1, inputs.pop(normal_i))
            tex_start = 2
            has_normal = True
        elif normal_i == 1:
            tex_start = 2
            has_normal = True
        else:
            tex_start = 1
            has_normal = False
            
        return [vertex_i, has_normal, tex_start, index, inputs]
