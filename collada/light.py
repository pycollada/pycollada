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

"""Light module, classes and tools."""

from xml.etree import ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag

class Light(DaeObject):
    """Abstract light class holding data from <light> tags."""

    @staticmethod
    def load(collada, localscope, node):
        tecnode = node.find( tag('technique_common') )
        if tecnode is None or len(tecnode) == 0: 
            raise DaeIncompleteError('Missing common technique in light')
        lightnode = tecnode[0]
        if lightnode.tag == tag('directional'):
            return SunLight.load( collada, localscope, node )
        elif lightnode.tag == tag('point'):
            return PointLight.load( collada, localscope, node )
        elif lightnode.tag == tag('ambient'):
            return AmbientLight.load( collada, localscope, node )
        else:
            raise DaeUnsupportedError('Unrecognized light type: %s'%lightnode.tag)

class SunLight(Light):
    """Directional light as defined in COLLADA tag <directional>."""

    def __init__(self, id, color, xmlnode = None):
        """Create a new sun light.

        :Parameters:
          id
            Id for the object
          color
            Light color
          xmlnode
            If load form xml, the xml node

        """
        self.id = id
        """Id in the light library."""
        # TODO: check if this is actually the initial direction
        self.direction = numpy.array( [0, 0, 1], dtype=numpy.float32 )
        """Incoming direction of the light."""
        self.color = color
        """Light color."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('light') )
            tecnode = ElementTree.Element( tag('technique_common') )
            self.xmlnode.append(tecnode)
            dirnode = ElementTree.Element( tag('directional') )
            tecnode.append( dirnode )
            colornode = ElementTree.Element( tag('color') )
            dirnode.append( colornode )
            colornode.text = ' '.join( [ str(v) for v in self.color ] )
            self.xmlnode.set('id', self.id)
            self.xmlnode.set('name', self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        colornode = self.xmlnode.find( '%s/%s/%s'%(tag('technique_common'),tag('directional'), 
                                                  tag('color') ) )
        colornode.text = ' '.join( [ str(v) for v in self.color ] )

        
    @staticmethod
    def load(collada, localscope, node):
        colornode = node.find( '%s/%s/%s'%(tag('technique_common'),tag('directional'), 
                                           tag('color') ) )
        if colornode is None: raise DaeIncompleteError('Missing color for directional light')
        try: color = tuple( [ float(v) for v in colornode.text.split() ] )
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted color values in light definition')
        return SunLight(node.get('id'), color, xmlnode = node)
    
    def bind(self, matrix):
        """Create a bound light of itself based on a transform matrix."""
        return BoundSunLight(self, matrix)

class AmbientLight(Light):
    """Ambient light as defined in COLLADA tag <ambient>."""

    def __init__(self, id, color, xmlnode = None):
        """Create a new ambient light.

        :Parameters:
          id
            Id for the object
          color
            Light color
          xmlnode
            If load form xml, the xml node

        """
        self.id = id
        """Id in the light library."""
        self.color = color
        """Light color."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('light') )
            tecnode = ElementTree.Element( tag('technique_common') )
            self.xmlnode.append(tecnode)
            dirnode = ElementTree.Element( tag('ambient') )
            tecnode.append( dirnode )
            colornode = ElementTree.Element( tag('color') )
            dirnode.append( colornode )
            colornode.text = ' '.join( [ str(v) for v in self.color ] )
            self.xmlnode.set('id', self.id)
            self.xmlnode.set('name', self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        colornode = self.xmlnode.find( '%s/%s/%s'%(tag('technique_common'),tag('ambient'), 
                                                  tag('color') ) )
        colornode.text = ' '.join( [ str(v) for v in self.color ] )

        
    @staticmethod
    def load(collada, localscope, node):
        colornode = node.find( '%s/%s/%s'%(tag('technique_common'),tag('ambient'), 
                                           tag('color') ) )
        if colornode is None: raise DaeIncompleteError('Missing color for ambient light')
        try: color = tuple( [ float(v) for v in colornode.text.split() ] )
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted color values in light definition')
        return AmbientLight(node.get('id'), color, xmlnode = node)
    
    def bind(self, matrix):
        """Create a bound light of itself based on a transform matrix."""
        return BoundAmbientLight(self, matrix)

class PointLight(Light):
    """Point light as defined in COLLADA tag <point>."""

    def __init__(self, id, color, constant_att, linear_att, quad_att, xmlnode = None):
        """Create a new sun light.

        :Parameters:
          id
            Id for the object
          color
            Light color
          constant_att
            Constant attenuation factor
          linear_att
            Linear attenuation factor
          quad_att
            Quadratic attenuation factor
          xmlnode
            If load form xml, the xml node

        """
        self.id = id
        """Id in the light library."""
        self.position = numpy.array( [0, 0, 0], dtype=numpy.float32 )
        """Location of the light."""
        self.color = color
        """Light color."""
        self.constant_att = constant_att
        """Constant attenuation factor."""
        self.linear_att = linear_att
        """Linear attenuation factor."""
        self.quad_att = quad_att
        """Quadratic attenuation factor."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('light') )
            tecnode = ElementTree.Element( tag('technique_common') )
            self.xmlnode.append(tecnode)
            pnode = ElementTree.Element( tag('point') )
            tecnode.append( pnode )

            colornode = ElementTree.Element( tag('color') )
            pnode.append( colornode )
            colornode.text = ' '.join( [ str(v) for v in self.color ] )

            attnode = ElementTree.Element( tag('constant_attenuation') )
            pnode.append( attnode )
            attnode.text = str(self.constant_att)

            attnode = ElementTree.Element( tag('linear_attenuation') )
            pnode.append( attnode )
            attnode.text = str(self.linear_att)

            attnode = ElementTree.Element( tag('quadratic_attenuation') )
            pnode.append( attnode )
            attnode.text = str(self.quad_att)

            self.xmlnode.set('id', self.id)
            self.xmlnode.set('name', self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        pnode = self.xmlnode.find( '%s/%s'%(tag('technique_common'),tag('point')) )
        colornode = pnode.find( tag('color') )
        colornode.text = ' '.join( [ str(v) for v in self.color ] )
        attnode = pnode.find( tag('constant_attenuation') )
        attnode.text = str(self.constant_att)
        attnode = pnode.find( tag('linear_attenuation') )
        attnode.text = str(self.linear_att)
        attnode = pnode.find( tag('quadratic_attenuation') )
        attnode.text = str(self.quad_att)

        
    @staticmethod
    def load(collada, localscope, node):
        pnode = node.find( '%s/%s'%(tag('technique_common'),tag('point')) )
        colornode = pnode.find( tag('color') )
        if colornode is None: raise DaeIncompleteError('Missing color for point light')
        try: color = tuple( [ float(v) for v in colornode.text.split() ] )
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted color values in light definition')
        constant_att = linear_att = quad_att = 0.0
        cattnode = pnode.find( tag('constant_attenuation') )
        lattnode = pnode.find( tag('linear_attenuation') )
        qattnode = pnode.find( tag('quadratic_attenuation') )
        try:
            if cattnode != None: constant_att = float(cattnode.text)
            if lattnode != None: linear_att = float(lattnode.text)
            if qattnode != None: quad_att = float(qattnode.text)
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted values in light definition')
        return PointLight(node.get('id'), color, constant_att, linear_att, 
                          quad_att, xmlnode = node)

    def bind(self, matrix):
        """Create a bound light of itself based on a transform matrix."""
        return BoundPointLight(self, matrix)

class BoundLight(object): pass

class BoundPointLight(object):
    """Point light bount to a scene with transformation."""

    def __init__(self, plight, matrix):
        self.position = numpy.dot( matrix[:3,:3], plight.position ) + matrix[:3,3]
        self.color = plight.color
        self.constant_att = plight.constant_att
        self.linear_att = plight.linear_att
        self.quad_att = plight.quad_att
        self.original = plight

    def __str__(self): return 'PointLight(at %s)' % str(self.position)
    def __repr__(self): return str(self)

class BoundSunLight(object):
    """Point light bount to a scene with transformation."""

    def __init__(self, slight, matrix):
        self.direction = numpy.dot( matrix[:3,:3], slight.direction )
        self.color = slight.color
        self.original = slight

    def __str__(self): return 'SunLight(from %s)' % str(self.direction)
    def __repr__(self): return str(self)

class BoundAmbientLight(object):
    """Ambient light bount to a scene with transformation."""

    def __init__(self, slight, matrix):
        self.color = slight.color
        self.original = slight

    def __str__(self): return 'AmbientLight'
    def __repr__(self): return str(self)
    