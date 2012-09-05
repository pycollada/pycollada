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

"""Contains objects for representing a kinematics scene."""

import numpy

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class KinematicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_scene> tag"""
    def __init__( self, id, kinematics_models=None, articulated_systems=None, collada=None):
        self.id = id
        """The unique string identifier for the scene"""

        self.collada = collada
        """The collada instance this is part of"""
        
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        return KinematicsScene(id)
    
    
