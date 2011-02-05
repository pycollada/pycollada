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

class Source(DaeObject):
    """Abstract class for loading source arrays"""
    
    @staticmethod
    def load(collada, localscope, node):
        sourceid = node.get('id')
        arraynode = node.find(tag('float_array'))
        if not arraynode is None:
            return FloatSource.load(collada, localscope, node)
        
        arraynode = node.find(tag('IDREF_array'))
        if not arraynode is None:
            return IDRefSource.load(collada, localscope, node)
        
        arraynode = node.find(tag('Name_array'))
        if not arraynode is None:
            return NameSource.load(collada, localscope, node)
        
        if arraynode is None: raise DaeIncompleteError('No array found in source %s' % sourceid)
        

class FloatSource(Source):
    """Source with float_array as it appears in <source> tag

    Instances of this class hold point and uv array data which are then
    used by primitives inside <geometry> tags.

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
            If loaded from XML, the corresponding node

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
            #U,V is used for "generic" arguments - convert to S,T
            components = ['S', 'T']
        return FloatSource( sourceid, data, tuple(components), xmlnode=node )

class IDRefSource(Source):
    """Source with IDREF_array as it appears in <source> tag

    Instances of this class hold strings that refer to other
    nodes in the document

    """

    def __init__(self, id, data, components, xmlnode=None):
        """Create a source instance.

        :Parameters:
          id
            Id for later access
          data
            List of strings, each a reference value
          components
            Tuple of strings describing the semantic of the data 
            like ('MORPH_TARGET')
          xmlnode
            If loaded from XML, the corresponding node

        """
          
        self.id = id
        """Object id in the global scope."""
        self.data = data
        """List of strings, each a reference value."""
        self.components = components
        """Tuple of strings describing the semantic of the data like ('MORPH_TARGET')."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('source') )
            self.xmlnode.set('id', self.id)
            arraynode = ElementTree.Element( tag('IDREF_array') )
            tecnode = ElementTree.Element( tag('technique_common') )
            accessor = ElementTree.Element( tag('accessor') )
            self.xmlnode.append(arraynode)
            tecnode.append(accessor)
            self.xmlnode.append(tecnode)
            for c in self.components:
                param = ElementTree.Element('param')
                param.set('type', 'IDREF')
                param.set('name', c )
                accessor.append( param )

    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i]

    def save(self):
        txtdata = ' '.join([ f for f in self.data ])
        node = self.xmlnode.find(tag('IDREF_array'))
        node.text = txtdata
        node.set('count', str(len(self.data)))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.set('count', str(len(self.components)))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        self.xmlnode.set('id', self.id )
    
    @staticmethod
    def load( collada, localscope, node ):
        sourceid = node.get('id')
        arraynode = node.find(tag('IDREF_array'))
        if arraynode is None: raise DaeIncompleteError('No IDREF_array in source node')
        if arraynode.text is None:
            values = []
        else:
            try: values = [v for v in arraynode.text.split()]
            except ValueError: raise DaeMalformedError('Corrupted IDREF array')
        data = values
        paramnodes = node.findall('%s/%s/%s'%(tag('technique_common'), tag('accessor'), tag('param')))
        if not paramnodes: raise DaeIncompleteError('No accessor info in source node')
        components = [ param.get('name') for param in paramnodes ]
        return IDRefSource( sourceid, data, tuple(components), xmlnode=node )

class NameSource(Source):
    """Source with Name_array as it appears in <source> tag

    Instances of this class hold strings

    """

    def __init__(self, id, data, components, xmlnode=None):
        """Create a source instance.

        :Parameters:
          id
            Id for later access
          data
            List of strings
          components
            Tuple of strings describing the semantic of the data 
            like ('JOINT')
          xmlnode
            If loaded from XML, the corresponding node

        """
          
        self.id = id
        """Object id in the global scope."""
        self.data = data
        """List of strings."""
        self.components = components
        """Tuple of strings describing the semantic of the data like ('JOINT')."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('source') )
            self.xmlnode.set('id', self.id)
            arraynode = ElementTree.Element( tag('Name_array') )
            tecnode = ElementTree.Element( tag('technique_common') )
            accessor = ElementTree.Element( tag('accessor') )
            self.xmlnode.append(arraynode)
            tecnode.append(accessor)
            self.xmlnode.append(tecnode)
            for c in self.components:
                param = ElementTree.Element('param')
                param.set('type', 'Name')
                param.set('name', c )
                accessor.append( param )

    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i]

    def save(self):
        txtdata = ' '.join([ f for f in self.data ])
        node = self.xmlnode.find(tag('Name_array'))
        node.text = txtdata
        node.set('count', str(len(self.data)))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.set('count', str(len(self.components)))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        self.xmlnode.set('id', self.id )
    
    @staticmethod
    def load( collada, localscope, node ):
        sourceid = node.get('id')
        arraynode = node.find(tag('Name_array'))
        if arraynode is None: raise DaeIncompleteError('No Name_array in source node')
        if arraynode.text is None:
            values = []
        else:
            try: values = [v for v in arraynode.text.split()]
            except ValueError: raise DaeMalformedError('Corrupted Name array')
        data = values
        paramnodes = node.findall('%s/%s/%s'%(tag('technique_common'), tag('accessor'), tag('param')))
        if not paramnodes: raise DaeIncompleteError('No accessor info in source node')
        components = [ param.get('name') for param in paramnodes ]
        return NameSource( sourceid, data, tuple(components), xmlnode=node )
