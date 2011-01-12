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

"""Camera module, class and tools."""

from xml.etree import ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, tag

class Camera(DaeObject):
    """Camera data as defined in COLLADA tag <camera>."""

    def __init__(self, id, fov, near, far, xmlnode = None):
        """Create a new camera.

        :Parameters:
          id
            Id for the object
          fov
            Y axis field of visiona in degrees
          near
            Near plane distance
          far
            Far plane distance
          xmlnode
            If load form xml, the xml node

        """
        self.id = id
        """Id in the camera library."""
        self.fov = fov
        """Field of vision in degrees."""
        self.near = near
        """Near plane distance."""
        self.far = far
        """Far plane distance."""
        self.position = numpy.array( [0, 0, 0], dtype=numpy.float32 )
        """Position in space of the point of view."""
        self.direction = numpy.array( [0, 0, -1], dtype=numpy.float32 )
        """Look direction of the camera."""
        self.up = numpy.array( [0, 1, 0], dtype=numpy.float32 )
        """Up vector of the camera."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('camera') )
            opticsnode = ElementTree.Element( tag('optics') )
            self.xmlnode.append( opticsnode )
            tecnode = ElementTree.Element( tag('technique_common') )
            opticsnode.append(tecnode)
            persnode = ElementTree.Element( tag('perspective') )
            tecnode.append( persnode )
            params = [ ElementTree.Element( tag(t) ) for t in ('yfov', 'znear', 'zfar') ]
            for p in params: persnode.append( p )
            p[0].text = str(self.fov)
            p[1].text = str(self.near)
            p[2].text = str(self.far)
            self.xmlnode.set('id', self.id)
            self.xmlnode.set('name', self.id)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        persnode = self.xmlnode.find( '%s/%s/%s'%(tag('optics'),tag('technique_common'), 
                                                  tag('perspective') ) )
        yfovnode = persnode.find( tag('yfov') )
        yfovnode.text = str(self.fov)
        if self.near:
            znearnode = persnode.find( tag('znear') )
            znearnode.text = str(self.near)
        if self.far:
            zfarnode = persnode.find( tag('zfar') )
            zfarnode.text = str(self.near)

        
    @staticmethod
    def load(collada, localscope, node):
        persnode = node.find( '%s/%s/%s'%(tag('optics'),tag('technique_common'), 
                                          tag('perspective') ))
        if persnode is None: raise DaeIncompleteError('Missing perspetive for camera definition')
        yfovnode = persnode.find( tag('yfov') )
        correction = 1.0
        if yfovnode != None: fov = yfovnode.text
        else:
            xfovnode = persnode.find( tag('xfov') )
            if xfovnode != None: 
                fov = xfovnode.text
                rationode = persnode.find( tag('aspect_ratio') )
                if rationode != None: correction = rationode.text
            else: fov = 45.0
        try:
            fov = float(fov)
            correction = float(correction)
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted float values in camera definition')
        fov *= correction
        znearnode = persnode.find( tag('znear') )
        zfarnode = persnode.find( tag('zfar') )
        try: 
            if znearnode != None: near = float(znearnode.text)
            else: near = None
            if zfarnode != None: far = float(zfarnode.text)
            else: far = None
        except ValueError, ex: 
            raise DaeMalformedError('Corrupted float values in camera definition')
        # KISS
        for n in persnode: 
            if n.tag in ['xfov', 'aspect_ratio']: persnode.remove(n)
        if yfovnode is None:
            yfovnode = ElementTree.Element(tag('yfov'))
            yfovnode.text = str(fov)
            persnode.append(yfovnode)
        return Camera(node.get('id'), fov, near, far, xmlnode = node)

    def bind(self, matrix):
        """Create a bound camera of itself based on a transform matrix."""
        return BoundCamera(self, matrix)

class BoundCamera(object):
    """Camera bound to a scene with a transform."""

    def __init__(self, cam, matrix):
        """Create a bound camera based on a transform matrix."""
        self.fov = cam.fov
        """Field of vision in degrees."""
        self.near = cam.near
        """Near plane distance."""
        self.far = cam.far
        """Far plane distance."""
        self.position = numpy.dot( matrix[:3,:3], cam.position ) + matrix[:3,3]
        """Position in space of the point of view."""
        self.direction = numpy.dot( matrix[:3,:3], cam.direction )
        """Look direction of the camera."""
        self.up = numpy.dot( matrix[:3,:3], cam.up )
        """Up vector of the camera."""
        self.original = cam
        """Original camera object from this object is a transformation."""
        dlen = numpy.sqrt(numpy.dot(self.direction, self.direction))
        ulen = numpy.sqrt(numpy.dot(self.up, self.up))
        if dlen > 0: self.direction /= dlen
        if ulen > 0: self.up /= ulen

    def __str__(self): return 'Camera(at %s)' % str(self.position)
    def __repr__(self): return str(self)
