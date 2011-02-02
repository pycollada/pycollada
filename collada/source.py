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

"""Module for managing data sources defined in geometry tags."""

from xml.etree import ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, tag

def cleanId( text ):
    if text and text[0] == '#': return text[1:]
    else: return text

class Source(DaeObject):
    """Data source as it appears in <source> tags inside geometry

    Instances of this class hold point and uv array data which are then
    used by primitives inside <geometry> tags. We only support float arrays 
    at the moment.

    """

    def __init__(self, id, data, components, xmlnode=None):
        """Create a source instance.

        :Parameters:
          id
            Id for later access
          data
            Numpy array with the flatten values (unshaped)
          components
            Tuple of strings describing the semantic of the data 
            like ('X','Y','Z')
          xmlnode
            If loaded from XML, the correponding node

        """
          
        self.id = id
        """Object id in the global scope."""
        self.data = data
        """Numpy array with the values."""
        self.data.shape = (-1, len(components) )
        self.components = components
        """Tuple of strings describing the semantic of the data like ('X','Y','Z')."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            #self.id = cid or ('basicsource' + str(id(self)))
            self.xmlnode = ElementTree.Element( tag('source') )
            self.xmlnode.set('id', self.id)
            arraynode = ElementTree.Element( tag('float_array') )
            tecnode = ElementTree.Element( tag('technique_common') )
            accessor = ElementTree.Element( tag('accessor') )
            self.xmlnode.append(arraynode)
            tecnode.append(accessor)
            self.xmlnode.append(tecnode)
            for c in self.components:
                param = ElementTree.Element('param')
                param.set('type', 'float')
                param.set('name', c )
                accessor.append( param )

    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i]

    def save(self):
        self.data.shape = (-1,)
        txtdata = ' '.join([ str(f) for f in self.data ])#str(self.data)[1:-1]
        rawlen = len( self.data )
        self.data.shape = (-1, len(self.components) )
        acclen = len( self.data )
        node = self.xmlnode.find(tag('float_array'))
        node.text = txtdata
        node.set('count', str(rawlen))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.set('count', str(acclen))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        self.xmlnode.set('id', self.id )
    
    @staticmethod
    def load( collada, localscope, node ):
        sourceid = node.get('id')
        arraynode = node.find(tag('float_array'))
        if arraynode is None: raise DaeIncompleteError('No float_array in source node')
        if arraynode.text is None:
            values = []
        else:
            try: values = [ float(v) for v in arraynode.text.split()]
            except ValueError: raise DaeMalformedError('Corrupted float array')
        data = numpy.array( values, dtype=numpy.float32 )
        paramnodes = node.findall('%s/%s/%s'%(tag('technique_common'), tag('accessor'), tag('param')))
        if not paramnodes: raise DaeIncompleteError('No accessor info in source node')
        components = [ param.get('name') for param in paramnodes ]
        if len(components) == 2 and components[0] == 'U' and components[1] == 'V':
            components = ['S', 'T'] #FIXME !!!!!
        source = Source( sourceid, data, tuple(components), xmlnode=node )
        return source

