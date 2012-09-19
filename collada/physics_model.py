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
    def __init__(self, id, name, rigid_bodies=None, physics_models=None, instance_physics_models=None, extras=None, xmlnode=None):
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

        self.extras = []
        if extras is not None:
            self.extras = extras
            
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
        id = node.get("id")
        name = node.get("name")
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
                        instance_physics_model = InstancePhysicsModel.load(collada,localscope,subnode)
            elif subnode.tag == tag('rigid_body'):
                # todo
                pass
            elif subnode.tag == tag('rigid_constraint'):
                # todo
                pass
        extras = Extra.loadextras(collada, node)
        node = PhysicsModel(id, name, rigid_bodies, physics_models, instance_physics_models, extras, xmlnode=node )
        return node

    def save(self):
        Extra.saveextras(self.xmlnode,self.extras)
        oldnodes = self.xmlnode.findall('%s/%s' % (tag('instance_physics_model'), tag('rigid_body')))
        for node in oldnodes:
            self.xmlnode.remove(oldnode)    
        for rigid_body in self.rigid_bodies:
            self.xmlnode.append(rigid_body.xmlnode)
        for physics_model in self.physics_models:
            ipm = E.instance_physics_model()
            ipm.set('url','#'+physics_model.id)
            self.xmlnode.append(ipm)
        for instance_physics_model in self.instance_physics_models:
            self.xmlnode.append(instance_physics_model.xmlnode)
            
        if self.id is not None:
            self.xmlnode.set('id',self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
