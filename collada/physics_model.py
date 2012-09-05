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

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .rigid_body import InstanceRigidBody

class InstancePhysicsModel(object):
    def __init__(self,url, sid=None, name=None, parent=None, instance_rigid_bodies=None, xmlnode=None):
        self.url = url
        self.sid = sid
        self.name = name
        self.parent = parent
        self.instance_rigid_bodies = []
        if instance_rigid_bodies is not None:
            self.instance_rigid_bodies = instance_rigid_bodies
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_physics_model()
            self.save()
            
    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        self.xmlnode.set('url',self.url)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
        if self.parent is not None:
            self.xmlnode.set('parent',self.parent)
        else:
            self.xmlnode.attrib.pop('parent')
            
    @staticmethod
    def load( collada, localscope, node ):
        instance_rigid_bodies = []
        for subnode in node:
            if subnode.tag == tag('instance_rigid_body'):
                pass
            
        return InstancePhysicsModel(node.get('url'),node.get('sid'), node.get('name'), node.get('parent'), instance_rigid_bodies, xmlnode=node) # external reference
        
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
        for subnode in node:
            if subnode.tag == tag('instance_physics_model'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'):
                        _physics_model = collada.physics_models.get(url[1:])
                        if _physics_model is None:
                            raise DaeBrokenRefError('physics_model %s not found in library'%url)

                        physics_models.append(_physics_model)
                    else:
                        instance_physics_model = InstancePhysicsModel.load(collada,localscope,node)
            elif subnode.tag == tag('rigid_body'):
                # todo
                pass
            elif subnode.tag == tag('rigid_constraint'):
                # todo
                pass
        node = PhysicsModel(collada, id, name, rigid_bodies, physics_models, instance_physics_models, xmlnode=node )
        return node
