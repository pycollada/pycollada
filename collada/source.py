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

"""Module for managing data sources defined in geometry tags."""

from lxml import etree as ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, tag, E

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
            self.data.shape = (-1,)
            txtdata = ' '.join([ str(f) for f in self.data ])
            rawlen = len( self.data )
            self.data.shape = (-1, len(self.components) )
            acclen = len( self.data )
            stridelen = len(self.components)
            sourcename = "%s-array"%self.id
            
            self.xmlnode = E.source(
                E.float_array(txtdata, count=str(rawlen), id=sourcename),
                E.technique_common(
                    E.accessor(
                        *[E.param(type='float', name=c) for c in self.components]
                    , **{'count':str(acclen), 'stride':str(stridelen), 'source':"#%s"%sourcename} )
                )
            , id=self.id )

    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i]

    def save(self):
        self.data.shape = (-1,)
        txtdata = ' '.join([ str(f) for f in self.data ])
        rawlen = len( self.data )
        self.data.shape = (-1, len(self.components) )
        acclen = len( self.data )
        node = self.xmlnode.find(tag('float_array'))
        node.text = txtdata
        node.set('count', str(rawlen))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.clear()
        node.set('count', str(acclen))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        for c in self.components:
            node.append(E.param(type='float', name=c))
        self.xmlnode.set('id', self.id )
    
    @staticmethod
    def load( collada, localscope, node ):
        sourceid = node.get('id')
        arraynode = node.find(tag('float_array'))
        if arraynode is None: raise DaeIncompleteError('No float_array in source node')
        if arraynode.text is None:
            data = numpy.array([], dtype=numpy.float32)
        else:
            try: data = numpy.fromstring(arraynode.text, dtype=numpy.float32, sep=' ')
            except ValueError: raise DaeMalformedError('Corrupted float array')
        paramnodes = node.findall('%s/%s/%s'%(tag('technique_common'), tag('accessor'), tag('param')))
        if not paramnodes: raise DaeIncompleteError('No accessor info in source node')
        components = [ param.get('name') for param in paramnodes ]
        if len(components) == 2 and components[0] == 'U' and components[1] == 'V':
            #U,V is used for "generic" arguments - convert to S,T
            components = ['S', 'T']
        if len(components) == 3 and components[0] == 'S' and components[1] == 'T' and components[2] == 'P':
            components = ['S', 'T']
            data.shape = (-1, 3)
            #remove 3d texcoord dimension because we don't support it
            #TODO
            data = numpy.array(zip(data[:,0], data[:,1]))
            data.shape = (-1)
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
            Numpy array of strings, each a reference value (unshaped)
          components
            Tuple of strings describing the semantic of the data 
            like ('MORPH_TARGET')
          xmlnode
            If loaded from XML, the corresponding node

        """
          
        self.id = id
        """Object id in the global scope."""
        self.data = data
        """Numpy array of strings, each a reference value."""
        self.data.shape = (-1, len(components) )
        self.components = components
        """Tuple of strings describing the semantic of the data like ('MORPH_TARGET')."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.data.shape = (-1,)
            txtdata = ' '.join([ str(f) for f in self.data ])
            rawlen = len( self.data )
            self.data.shape = (-1, len(self.components) )
            acclen = len( self.data )
            stridelen = len(self.components)
            sourcename = "%s-array"%self.id
            
            self.xmlnode = E.source(
                E.IDREF_array(txtdata, count=str(rawlen), id=sourcename),
                E.technique_common(
                    E.accessor(
                        *[E.param(type='IDREF', name=c) for c in self.components]
                    , **{'count':str(acclen), 'stride':str(stridelen), 'source':sourcename})
                )
            , id=self.id )

    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i][0] if len(self.data[i])==1 else self.data[i]

    def save(self):
        self.data.shape = (-1,)
        txtdata = ' '.join([ str(f) for f in self.data ])
        rawlen = len( self.data )
        self.data.shape = (-1, len(self.components) )
        acclen = len( self.data )
        
        node = self.xmlnode.find(tag('IDREF_array'))
        node.text = txtdata
        node.set('count', str(rawlen))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.clear()
        node.set('count', str(acclen))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        for c in self.components:
            node.append(E.param(type='IDREF', name=c))
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
        data = numpy.array( values, dtype=numpy.string_ )
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
            Numpy array of strings (unshaped)
          components
            Tuple of strings describing the semantic of the data 
            like ('JOINT')
          xmlnode
            If loaded from XML, the corresponding node

        """
          
        self.id = id
        """Object id in the global scope."""
        self.data = data
        """Numpy array of strings."""
        self.data.shape = (-1, len(components) )
        self.components = components
        """Tuple of strings describing the semantic of the data like ('JOINT')."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.data.shape = (-1,)
            txtdata = ' '.join([ str(f) for f in self.data ])
            rawlen = len( self.data )
            self.data.shape = (-1, len(self.components) )
            acclen = len( self.data )
            stridelen = len(self.components)
            sourcename = "%s-array"%self.id
            
            self.xmlnode = E.source(
                E.Name_array(txtdata, count=str(rawlen), id=sourcename),
                E.technique_common(
                    E.accessor(
                        *[E.param(type='Name', name=c) for c in self.components]
                    , **{'count':str(acclen), 'stride':str(stridelen), 'source':sourcename})
                )
            , id=self.id )
            
    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i][0] if len(self.data[i])==1 else self.data[i]

    def save(self):
        self.data.shape = (-1,)
        txtdata = ' '.join([ str(f) for f in self.data ])
        rawlen = len( self.data )
        self.data.shape = (-1, len(self.components) )
        acclen = len( self.data )

        node = self.xmlnode.find(tag('Name_array'))
        node.text = txtdata
        node.set('count', str(rawlen))
        node.set('id', self.id+'-array' )
        node = self.xmlnode.find('%s/%s'%(tag('technique_common'), tag('accessor')))
        node.clear()
        node.set('count', str(acclen))
        node.set('source', '#'+self.id+'-array')
        node.set('stride', str(len(self.components)))
        for c in self.components:
            node.append(E.param(type='IDREF', name=c))
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
        data = numpy.array( values, dtype=numpy.string_ )
        paramnodes = node.findall('%s/%s/%s'%(tag('technique_common'), tag('accessor'), tag('param')))
        if not paramnodes: raise DaeIncompleteError('No accessor info in source node')
        components = [ param.get('name') for param in paramnodes ]
        return NameSource( sourceid, data, tuple(components), xmlnode=node )
