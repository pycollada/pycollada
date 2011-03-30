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

"""Module for <geometry> data loading."""

from lxml import etree as ElementTree
import numpy
import source
import triangleset
import lineset
import polylist
import polygons
import types
import primitive
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag, E

class Geometry( DaeObject ):
    """A class containing the data coming from a COLLADA <geometry> tag"""

    def __init__(self, collada, id, name, sourcebyid, primitives=[], xmlnode=None):
        """Create a geometry instance

        :Parameters:
          collada
            The collada object this geometry belongs to
          id
            A unique identifier for the geometry
          name
            A text string naming the geometry
          sourcebyid
            A list of Source objects or
            a dictionary mapping source ids to the actual objects
          primitives
            List of primitive objects contained
          xmlnode
            When loaded, the xmlnode it comes from

        """
        
        self.collada = collada
        """The collada object this geometry belongs to"""
        
        self.id = id
        """A unique identifier for the geometry"""
        
        self.name = name
        """A text string naming the geometry"""

        self.sourceById = sourcebyid
        """Sources indexed by id."""

        if type(sourcebyid) is types.ListType:
            self.sourceById = {}
            for src in sourcebyid:
                self.sourceById[src.id] = src
        
        self.primitives = primitives
        """Primitive object list inside this geometry."""
        
        if xmlnode != None: 
            self.xmlnode = xmlnode
        else:
            sourcenodes = []
            verticesnode = None
            for srcid, src in self.sourceById.iteritems():
                sourcenodes.append(src.xmlnode)
                if verticesnode is None:
                    #pick first source to be in the useless <vertices> tag
                    verticesnode = E.vertices(E.input(semantic='POSITION', source="#%s"%srcid),
                                              id=srcid + '-vertices')
            meshnode = E.mesh(*sourcenodes)
            meshnode.append(verticesnode)
            self.xmlnode = E.geometry(meshnode)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    def createLineSet(self, indices, inputlist, materialid):
        """Add a set of lines to this geometry instance.
        
        :Parameters:
          indices
            unshaped numpy array that contains the indices for
            the inputs referenced in inputlist
          inputlist
            InputList object that refers to the inputs for this primitive
          materialid
            A string containing a symbol that will get used to bind this lineset
            to a material when instantiating into a scene
            
        :Returns:
          A LineSet object
        """
        inputdict = primitive.Primitive.getInputsFromList(self.sourceById, inputlist.getList())
        return lineset.LineSet(inputdict, materialid, indices)

    def createTriangleSet(self, indices, inputlist, materialid):
        """Add a set of triangles to this geometry instance.
        
        :Parameters:
          indices
            unshaped numpy array that contains the indices for
            the inputs referenced in inputlist
          inputlist
            InputList object that refers to the inputs for this primitive
          materialid
            A string containing a symbol that will get used to bind this triangleset
            to a material when instantiating into a scene
            
        :Returns:
          A TriangleSet object
        """
        inputdict = primitive.Primitive.getInputsFromList(self.sourceById, inputlist.getList())
        return triangleset.TriangleSet(inputdict, materialid, indices)

    def createPolyList(self, indices, vcounts, inputlist, materialid):
        """Add a list of polygons to this geometry instance.
        
        :Parameters:
          indices
            unshaped numpy array that contains the indices for
            the inputs referenced in inputlist
          vcounts
            unshaped numpy array that contains the vertex count
            for each polygon in this polylist
          inputlist
            InputList object that refers to the inputs for this primitive
          materialid
            A string containing a symbol that will get used to bind this polylist
            to a material when instantiating into a scene
            
        :Returns:
          A TriangleSet object
        """
        inputdict = primitive.Primitive.getInputsFromList(self.sourceById, inputlist.getList())
        return polylist.Polylist(inputdict, materialid, indices, vcounts)

    def createPolygons(self, indices, inputlist, materialid):
        """Add a list of polygons to this geometry instance.
        
        :Parameters:
          indices
            list of unshaped numpy arrays that each contain the indices for
            a single polygon
          inputlist
            InputList object that refers to the inputs for this primitive
          materialid
            A string containing a symbol that will get used to bind this polylist
            to a material when instantiating into a scene
            
        :Returns:
          A Polygons object
        """
        inputdict = primitive.Primitive.getInputsFromList(self.sourceById, inputlist.getList())
        return polygons.Polygons(inputdict, materialid, indices)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id") or ""
        name = node.get("name") or ""
        meshnode = node.find(tag('mesh'))
        if meshnode is None: raise DaeUnsupportedError('Unknown geometry node')
        sourcebyid = {}
        sources = []
        sourcenodes = node.findall('%s/%s'%(tag('mesh'), tag('source')))
        for sourcenode in sourcenodes:
            ch = source.Source.load(collada, {}, sourcenode)
            sources.append(ch)
            sourcebyid[ch.id] = ch
            
        verticesnode = meshnode.find(tag('vertices'))
        if verticesnode is None:
            vertexsource = None
        else:
            inputnodes = {}
            for inputnode in verticesnode.findall(tag('input')):
                semantic = inputnode.get('semantic')
                inputsource = inputnode.get('source')
                if not semantic or not inputsource or not inputsource.startswith('#'):
                    raise DaeIncompleteError('Bad input definition inside vertices')
                inputnodes[semantic] = sourcebyid.get(inputsource[1:])
            if (not verticesnode.get('id') or len(inputnodes)==0 or 
                not 'POSITION' in inputnodes):
                raise DaeIncompleteError('Bad vertices definition in mesh')
            sourcebyid[verticesnode.get('id')] = inputnodes
            vertexsource = verticesnode.get('id')
            
        _primitives = []
        for subnode in meshnode:
            if subnode.tag == tag('polylist'):
                _primitives.append( polylist.Polylist.load( collada, sourcebyid, subnode ) )
            elif subnode.tag == tag('triangles'):
                _primitives.append( triangleset.TriangleSet.load( collada, sourcebyid, subnode ) )
            elif subnode.tag == tag('lines'):
                _primitives.append( lineset.LineSet.load( collada, sourcebyid, subnode ) )
            elif subnode.tag == tag('polygons'):
                _primitives.append( polygons.Polygons.load( collada, sourcebyid, subnode ) )
            elif subnode.tag != tag('source') and subnode.tag != tag('vertices') and subnode.tag != tag('extra'):
                raise DaeUnsupportedError('Unknown geometry tag %s' % subnode.tag)
        geom = Geometry(collada, id, name, sourcebyid, _primitives, xmlnode=node )
        return geom

    def save(self):
        meshnode = self.xmlnode.find(tag('mesh'))
        for src in self.sourceById.itervalues():
            if isinstance(src, source.Source):
                src.save()
                if src.xmlnode not in meshnode.getchildren():
                    meshnode.insert(0, src.xmlnode)
        
        deletenodes = []
        for oldsrcnode in meshnode.findall( tag('source') ):
            if oldsrcnode not in [src.xmlnode for src in self.sourceById.itervalues() if isinstance(src, source.Source)]:
                deletenodes.append(oldsrcnode)
        for d in deletenodes:
            meshnode.remove(d)
        
        vnode = self.xmlnode.find(tag('mesh')).find(tag('vertices'))
        input_vnode = vnode.find(tag('input'))
        srcref = input_vnode.get('source')[1:]
        if srcref not in self.sourceById:
            newsrcref = list(self.sourceById.iterkeys())[0]
            input_vnode.set('source', "#%s" % newsrcref)
            vnode.set('id', "#%s-vertices" % newsrcref)

        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.name)
        
        for prim in self.primitives:
            if prim.xmlnode not in meshnode.getchildren():
                meshnode.append(prim.xmlnode)
                
        deletenodes = []
        primnodes = [prim.xmlnode for prim in self.primitives]
        for child in meshnode.getchildren():
            if child.tag != tag('vertices') and child.tag != tag('source') and child not in primnodes:
                deletenodes.append(child)
        for d in deletenodes:
            meshnode.remove(d)

    def bind(self, matrix, materialnodebysymbol):
        """Create a bound geometry from this one, transform and material mapping"""
        return BoundGeometry(self, matrix, materialnodebysymbol)

class BoundGeometry( object ):
    """A geometry bound to a transform matrix and materials mapping."""

    def __init__(self, geom, matrix, materialnodebysymbol):
        """Create a bound geometry from a geometry, transform and material mapping"""
        self.matrix = matrix
        self.materialnodebysymbol = materialnodebysymbol
        self._primitives = geom.primitives
        self.original = geom

    def __len__(self): return len(self._primitives)

    def primitives(self):
        """Iterate through all the primitives inside the geometry."""
        for p in self._primitives:
            boundp = p.bind( self.matrix, self.materialnodebysymbol )
            yield boundp
