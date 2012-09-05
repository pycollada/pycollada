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

"""Contains objects for representing a physics model."""

import numpy

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class PhysicsModel(DaeObject):
    """A class containing the data coming from a COLLADA <physics_model> tag"""
    def __init__(self, collada, id, name, rigid_bodies=None, physics_models=None, instance_physics_models=None, xmlnode=None):
        """Create a physics_model instance

          :param collada.Collada collada:
            The collada object this geometry belongs to
          :param str id:
            A unique string identifier for the geometry
          :param str name:
            A text string naming the geometry
          :param list rigid_bodies: list of RigidBody
          :param list physics_models: list of PhysicsModel
          :param list instance_physics_models: list of InstancePhysicsModel
          :param xmlnode:
            When loaded, the xmlnode it comes from.

        """
        self.collada = collada
        """The :class:`collada.Collada` object this geometry belongs to"""

        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.rigid_bodies = []
        if rigid_bodies is not None:
            self.rigid_bodies = rigid_bodies

        self.physics_models = []
        if physics_models is not None:
            self.physics_models = physics_models

        self.instance_physics_models = []
        if instance_physics_models is not None:
            self.instance_physics_models = instance_physics_models
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.physics_model()
            for rigid_body in self.rigid_bodies:
                self.xmlnode.append(rigid_body.xmlnode)
            for physics_model in self.physics_models:
                self.xmlnode.append(physics_model.xmlnode)
            for instance_physics_model in self.instance_physics_models:
                self.xmlnode.append(instance_physics_model.xmlnode)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id") or ""
        name = node.get("name") or ""
        rigid_bodies = []
        physics_models = []
        instance_physics_models = []
        node = PhysicsModel(collada, id, name, rigid_bodies, physics_models, instance_physics_models, xmlnode=node )
        return node
