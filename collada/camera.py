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

"""Contains objects for representing cameras"""

from lxml import etree as ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, tag, E

class Camera(DaeObject):
    """Camera data as defined in COLLADA tag <camera>."""

    def __init__(self, id, fov, near, far, xmlnode = None):
        """Create a new camera.

        :param str id:
          Id for the object
        :param float fov:
          Y axis field of vision in degrees
        :param float near:
          Near plane distance
        :param float far:
          Far plane distance
        :param xmlnode:
          If loaded from xml, the xml node

        """
        self.id = id
        """Id in the camera library."""
        self.fov = fov
        """Field of vision in degrees."""
        self.near = near
        """Near plane distance."""
        self.far = far
        """Far plane distance."""
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the data."""
        else:
            self.xmlnode = E.camera(
                E.optics(
                    E.technique_common(
                        E.perspective(
                            E.yfov(str(self.fov)),
                            E.znear(str(self.near)),
                            E.zfar(str(self.far))
                        )
                    )
                )
            , id=self.id, name=self.id)

    def save(self):
        """Saves the camera's properties back to xmlnode"""
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
            zfarnode.text = str(self.far)

        
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
        for n in persnode: 
            if n.tag in ['xfov', 'aspect_ratio']: persnode.remove(n)
        if yfovnode is None:
            yfovnode = ElementTree.Element(tag('yfov'))
            yfovnode.text = str(fov)
            persnode.append(yfovnode)
        return Camera(node.get('id'), fov, near, far, xmlnode = node)

    def bind(self, matrix):
        """Create a bound camera of itself based on a transform matrix.
        
        :param numpy.array matrix:
          A numpy transformation matrix of size 4x4
          
        :rtype: :class:`collada.camera.BoundCamera`
        
        """
        return BoundCamera(self, matrix)

    def __str__(self): return 'Camera id=%s' % self.id
    def __repr__(self): return str(self)

class BoundCamera(object):
    """Camera bound to a scene with a transform. This gets created when a
        camera is instantiated in a scene. Do not create this manually."""

    def __init__(self, cam, matrix):
        self.fov = cam.fov
        """Field of vision in degrees."""
        self.near = cam.near
        """Near plane distance."""
        self.far = cam.far
        """Far plane distance."""
        self.matrix = matrix
        """The matrix bound to"""
        self.original = cam
        """Original :class:`collada.camera.Camera` object this is bound to."""

    def __str__(self): return 'BoundCamera bound to %s' % self.original.id
    def __repr__(self): return str(self)
