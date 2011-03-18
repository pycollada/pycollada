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

from lxml import etree as ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag, E

class Light(DaeObject):
    """Abstract light class holding data from <light> tags."""

    @staticmethod
    def _correctValInNode(outernode, tagname, value):
        innernode = outernode.find( tag(tagname) )
        if value is None and innernode is not None:
            outernode.remove(innernode)
        elif innernode is not None:
            innernode.text = str(value)
        elif value is not None:
            outernode.append(E(tagname, str(value)))

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
        elif lightnode.tag == tag('spot'):
            return SpotLight.load( collada, localscope, node )
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
            If loaded from xml, the xml node

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
            self.xmlnode = E.light(
                E.technique_common(
                    E.directional(
                        E.color(' '.join( [ str(v) for v in self.color ] ))
                    )
                )
            , id=self.id, name=self.id)

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
            If loaded from xml, the xml node

        """
        self.id = id
        """Id in the light library."""
        self.color = color
        """Light color."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = E.light(
                E.technique_common(
                    E.ambient(
                        E.color(' '.join( [ str(v) for v in self.color ] ))
                    )
                )
            , id=self.id, name=self.id)

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

    def __init__(self, id, color, quad_att, constant_att=None, linear_att=None, zfar=None, xmlnode = None):
        """Create a new sun light.

        :Parameters:
          id
            Id for the object
          color
            Light color
          quad_att
            Quadratic attenuation factor
          constant_att
            Constant attenuation factor
          linear_att
            Linear attenuation factor
          zfar
            Distance to the far clipping plane
          xmlnode
            If loaded from xml, the xml node

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
        self.zfar = zfar
        """Distance to the far clipping plane"""
        
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            pnode = E.point(
                E.color(' '.join( [ str(v) for v in self.color ] )),
                E.quadratic_attenuation(str(self.quad_att))
            )
            if self.constant_att is not None:
                pnode.append(E.constant_attenuation(str(self.constant_att)))
            if self.linear_att is not None:
                pnode.append(E.linear_attenuation(str(self.linear_att)))
            if self.zfar is not None:
                pnode.append(E.zfar(str(self.zvar)))
            
            self.xmlnode = E.light(
                E.technique_common(pnode)
            , id=self.id, name=self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        pnode = self.xmlnode.find( '%s/%s'%(tag('technique_common'),tag('point')) )
        colornode = pnode.find( tag('color') )
        colornode.text = ' '.join( [ str(v) for v in self.color ] )
        attnode = pnode.find( tag('quadratic_attenuation') )
        attnode.text = str(self.quad_att)
        Light._correctValInNode(pnode, 'constant_attenuation', self.constant_att)
        Light._correctValInNode(pnode, 'linear_attenuation', self.linear_att)
        Light._correctValInNode(pnode, 'zfar', self.zfar)

    @staticmethod
    def load(collada, localscope, node):
        pnode = node.find( '%s/%s'%(tag('technique_common'),tag('point')) )
        colornode = pnode.find( tag('color') )
        if colornode is None: raise DaeIncompleteError('Missing color for point light')
        try: color = tuple( [ float(v) for v in colornode.text.split() ] )
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted color values in light definition')
        constant_att = linear_att = zfar = None
        qattnode = pnode.find( tag('quadratic_attenuation') )
        if qattnode is None:
            raise DaeMalformedError('Point light requires quadratic attenuation')
        cattnode = pnode.find( tag('constant_attenuation') )
        lattnode = pnode.find( tag('linear_attenuation') )
        zfarnode = pnode.find( tag('zfar') )
        try:
            quad_att = float(qattnode.text)
            if cattnode is not None: constant_att = float(cattnode.text)
            if lattnode is not None: linear_att = float(lattnode.text)
            if zfarnode is not None: zfar = float(zfarnode.text)
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted values in light definition')
        return PointLight(node.get('id'), color, quad_att, constant_att, linear_att, 
                          zfar, xmlnode = node)

    def bind(self, matrix):
        """Create a bound light of itself based on a transform matrix."""
        return BoundPointLight(self, matrix)
    
class SpotLight(Light):
    """Spot light as defined in COLLADA tag <spot>."""

    def __init__(self, id, color, constant_att=None, linear_att=None, quad_att=None,
                    falloff_ang=None, falloff_exp=None, xmlnode = None):
        """Create a new spot light.

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
          falloff_ang
            Falloff angle
          falloff_exp
            Falloff exponent
          xmlnode
            If loaded from xml, the xml node

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
        self.falloff_ang = falloff_ang
        """Falloff angle"""
        self.falloff_exp = falloff_exp
        """Falloff exponent"""
        
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            pnode = E.spot(
                E.color(' '.join( [ str(v) for v in self.color ] )),
            )
            if self.constant_att is not None:
                pnode.append(E.constant_attenuation(str(self.constant_att)))
            if self.linear_att is not None:
                pnode.append(E.linear_attenuation(str(self.linear_att)))
            if self.quad_att is not None:
                pnode.append(E.quadratic_attenuation(str(self.quad_att)))
            if self.falloff_ang is not None:
                pnode.append(E.falloff_angle(str(self.falloff_ang)))
            if self.falloff_exp is not None:
                pnode.append(E.falloff_exponent(str(self.falloff_exp)))
            
            self.xmlnode = E.light(
                E.technique_common(pnode)
            , id=self.id, name=self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        pnode = self.xmlnode.find( '%s/%s'%(tag('technique_common'),tag('spot')) )
        colornode = pnode.find( tag('color') )
        colornode.text = ' '.join( [ str(v) for v in self.color ] )
        Light._correctValInNode(pnode, 'constant_attenuation', self.constant_att)
        Light._correctValInNode(pnode, 'linear_attenuation', self.linear_att)
        Light._correctValInNode(pnode, 'quadratic_attenuation', self.quad_att)
        Light._correctValInNode(pnode, 'falloff_angle', self.falloff_ang)
        Light._correctValInNode(pnode, 'falloff_exponent', self.falloff_exp)

    @staticmethod
    def load(collada, localscope, node):
        pnode = node.find( '%s/%s'%(tag('technique_common'),tag('spot')) )
        colornode = pnode.find( tag('color') )
        if colornode is None: raise DaeIncompleteError('Missing color for spot light')
        try: color = tuple( [ float(v) for v in colornode.text.split() ] )
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted color values in spot light definition')
        constant_att = linear_att = quad_att = falloff_ang = falloff_exp = None
        cattnode = pnode.find( tag('constant_attenuation') )
        lattnode = pnode.find( tag('linear_attenuation') )
        qattnode = pnode.find( tag('quadratic_attenuation') )
        fangnode = pnode.find( tag('falloff_angle') )
        fexpnode = pnode.find( tag('falloff_exponent') )
        try:
            if cattnode is not None: constant_att = float(cattnode.text)
            if lattnode is not None: linear_att = float(lattnode.text)
            if qattnode is not None: quad_att = float(qattnode.text)
            if fangnode is not None: falloff_ang = float(fangnode.text)
            if fexpnode is not None: falloff_exp = float(fexpnode.text)
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted values in spot light definition')
        return SpotLight(node.get('id'), color, constant_att, linear_att, quad_att,
                          falloff_ang, falloff_exp, xmlnode = node)

    def bind(self, matrix):
        """Create a bound light of itself based on a transform matrix."""
        return BoundSpotLight(self, matrix)

class BoundLight(object): pass

class BoundPointLight(object):
    """Point light bount to a scene with transformation."""

    def __init__(self, plight, matrix):
        self.position = numpy.dot( matrix[:3,:3], plight.position ) + matrix[:3,3]
        self.color = plight.color
        self.constant_att = plight.constant_att
        self.linear_att = plight.linear_att
        self.quad_att = plight.quad_att
        self.zfar = plight.zfar
        self.original = plight

    def __str__(self): return 'BoundPointLight(at %s)' % str(self.position)
    def __repr__(self): return str(self)
    
class BoundSpotLight(object):
    """Spot light bount to a scene with transformation."""

    def __init__(self, slight, matrix):
        self.position = numpy.dot( matrix[:3,:3], slight.position ) + matrix[:3,3]
        self.color = slight.color
        self.constant_att = slight.constant_att
        self.linear_att = slight.linear_att
        self.quad_att = slight.quad_att
        self.falloff_ang = slight.falloff_ang
        self.falloff_exp = slight.falloff_exp
        self.original = slight

    def __str__(self): return 'BoundSpotLight(at %s)' % str(self.position)
    def __repr__(self): return str(self)

class BoundSunLight(object):
    """Point light bount to a scene with transformation."""

    def __init__(self, slight, matrix):
        self.direction = numpy.dot( matrix[:3,:3], slight.direction )
        self.color = slight.color
        self.original = slight

    def __str__(self): return 'BoundSunLight(from %s)' % str(self.direction)
    def __repr__(self): return str(self)

class BoundAmbientLight(object):
    """Ambient light bount to a scene with transformation."""

    def __init__(self, slight, matrix):
        self.color = slight.color
        self.original = slight

    def __str__(self): return 'BoundAmbientLight'
    def __repr__(self): return str(self)
    