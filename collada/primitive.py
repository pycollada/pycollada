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
from collada import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, \
                    DaeUnsupportedError, DaeObject
import numpy
import types

class InputList(DaeObject):
    class Input:
        def __init__(self, offset, semantic, src, set=None):
            self.offset = offset
            self.semantic = semantic
            self.source = src
            self.set = set
    
    semantics = ["VERTEX", "NORMAL", "TEXCOORD", "TEXBINORMAL", "TEXTANGENT", "COLOR", "TANGENT", "BINORMAL"]
    
    def __init__(self):
        self.inputs = {}
        for s in self.semantics:
            self.inputs[s] = []
            
    def addInput(self, offset, semantic, src, set=None):
        if semantic not in self.semantics:
            raise DaeUnsupportedError("Unsupported semantic %s" % semantic)
        self.inputs[semantic].append(self.Input(offset, semantic, src, set))
        
    def getList(self):
        retlist = []
        for inplist in self.inputs.itervalues():
            for inp in inplist:
                 retlist.append((inp.offset, inp.semantic, inp.source, inp.set))
        return retlist

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
    def getInputsFromList(localscope, inputs):
        #first let's save any of the source that are references to a dict
        to_append = []
        for input in inputs:
            offset, semantic, source, set = input
            if semantic == 'VERTEX':
                vertex_source = localscope.get(source[1:])
                if type(vertex_source) == types.DictType:
                    for inputsemantic, inputsource in vertex_source.items():
                        if inputsemantic == 'POSITION':
                            to_append.append([offset, 'VERTEX', '#' + inputsource.id, set])
                        else:
                            to_append.append([offset, inputsemantic, '#' + inputsource.id, set])
        
        #remove all the dicts
        inputs[:] = [input for input in inputs if not type(localscope.get(input[2][1:])) is types.DictType]

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
        
        for input in inputs:
            offset, semantic, source, set = input
            if len(source) < 2 or source[0] != '#':
                raise DaeMalformedError('Incorrect source id "%s" in input' % source)
            if source[1:] not in localscope:
                raise DaeBrokenRefError('Source input id "%s" not found'%source)
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
                raise DaeUnsupportedError('Unknown input semantic: %s' % semantic)
            
        all_inputs = {}
        all_inputs['VERTEX'] = vertex_inputs
        all_inputs['NORMAL'] = normal_inputs
        all_inputs['TEXCOORD'] = texcoord_inputs
        all_inputs['TEXBINORMAL'] = textangent_inputs
        all_inputs['TEXTANGENT'] = textangent_inputs
        all_inputs['COLOR'] = color_inputs
        all_inputs['TANGENT'] = tangent_inputs
        all_inputs['BINORMAL'] = binormal_inputs
        
        return all_inputs

    @staticmethod
    def getInputs(localscope, inputnodes):
        try: 
            inputs = [ (int(i.get('offset')), i.get('semantic'), i.get('source'), i.get('set')) 
                           for i in inputnodes ]
        except ValueError, ex: raise DaeMalformedError('Corrupted offsets in primitive')
        
        return Primitive.getInputsFromList(localscope, inputs)
