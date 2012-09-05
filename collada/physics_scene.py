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
"""Contains objects for representing a physics scene."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class PhysicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <physics_scene> tag"""
    def __init__(self, collada, id, physics_models=None, xmlnode=None):
        """Create a scene

        :param str id:
          A unique string identifier for the scene
        :param list nodes:
          A list of type :class:`collada.scene.Node` representing the nodes in the scene
        :param xmlnode:
          When loaded, the xmlnode it comes from
        :param collada:
          The collada instance this is part of

        """
        self.id = id
        """The unique string identifier for the scene"""
        self.physics_models=physics_models
        
        self.collada = collada
        """The collada instance this is part of"""
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the scene node."""
        else:
            pass
        
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        return PhysicsScene(collada, id)
    
    
