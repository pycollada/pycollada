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

from .common import DaeObject, E, tag, save_attribute, save_child_object
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .rigid_body import InstanceRigidBody, RigidBody
from .extra import Extra

class InstancePhysicsModel(DaeObject):
    def __init__(self, pmodel=None, url=None, sid=None, name=None, parent=None, instance_rigid_bodies=None, extras=None, xmlnode=None):
        self.pmodel = pmodel
        self.url = url
        self.sid = sid
        self.name = name
        self.parent = parent
        self.instance_rigid_bodies = []
        if instance_rigid_bodies is not None:
            self.instance_rigid_bodies = instance_rigid_bodies
        self.extras = []
        if extras is not None:
            self.extras = extras
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_physics_model()
            self.save(0)
            
    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.pmodel is not None and self.pmodel.id is not None:
            self.xmlnode.set('url','#'+self.pmodel.id)
        elif self.url is not None:
            self.xmlnode.set('url',self.url)
        else:
            self.xmlnode.attrib.pop('url',None)
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
        url = node.get('url')
        name = node.get('name')
        pmodel = None
        if url is not None:
            if url.startswith('#'): # inside this doc, so search for it
                pmodel = collada.physics_models.get(url[1:])
                if pmodel is None:
                    raise DaeBrokenRefError('physics_model %s not found in library'%url)
                
                if name is not None:
                    pmodel = copy.copy(pmodel)
                    pmodel.name = name
        
        instance_rigid_bodies = []
        for subnode in node:
            if subnode.tag == tag('instance_rigid_body'):
                pass
        extras = Extra.loadextras(collada, node)
        return InstancePhysicsModel(pmodel,url,node.get('sid'), name, node.get('parent'), instance_rigid_bodies, extras, xmlnode=node) # external reference
        
class PhysicsModel(DaeObject):
    """A class containing the data coming from a COLLADA <physics_model> tag"""
    def __init__(self, id, name, rigid_bodies=None, instance_physics_models=None, extras=None, xmlnode=None):
        """Create a physics_model instance

          :param collada.Collada collada:
            The collada object this geometry belongs to
          :param str id:
            A unique string identifier for the geometry
          :param str name:
            A text string naming the geometry
          :param list rigid_bodies: list of RigidBody
          :param list instance_physics_models: list of InstancePhysicsModel
          :param xmlnode:
            When loaded, the xmlnode it comes from.

        """
        """The :class:`collada.Collada` object this geometry belongs to"""

        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.rigid_bodies = []
        if rigid_bodies is not None:
            self.rigid_bodies = rigid_bodies

        self.instance_physics_models = []
        if instance_physics_models is not None:
            self.instance_physics_models = instance_physics_models

        self.extras = []
        if extras is not None:
            self.extras = extras
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.physics_model()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id")
        name = node.get("name")
        rigid_bodies = []
        instance_physics_models = []
        for subnode in node:
            if subnode.tag == tag('instance_physics_model'):
                instance_physics_models.append(InstancePhysicsModel.load(collada, localscope, subnode))
            elif subnode.tag == tag('rigid_body'):
                rigid_bodies.append(RigidBody.load(collada,localscope,subnode))
            elif subnode.tag == tag('rigid_constraint'):
                # todo
                pass
        extras = Extra.loadextras(collada, node)
        return PhysicsModel(id, name, rigid_bodies, instance_physics_models, extras, xmlnode=node )

    def save(self, recurse=True):
        Extra.saveextras(self.xmlnode,self.extras)
        oldnodes = self.xmlnode.findall(tag('instance_physics_model'))+self.xmlnode.findall(tag('rigid_body'))
        for oldnode in oldnodes:
            self.xmlnode.remove(oldnode)    
        for rigid_body in self.rigid_bodies:
            if recurse:
                rigid_body.save(recurse)
            self.xmlnode.append(rigid_body.xmlnode)
        for instance_physics_model in self.instance_physics_models:
            if recurse:
                instance_physics_model.save(recurse)
            self.xmlnode.append(instance_physics_model.xmlnode)

        save_attribute(self.xmlnode,'id',self.id)
        save_attribute(self.xmlnode,'name',self.name)
