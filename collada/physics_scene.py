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
from .physics_model import InstancePhysicsModel
from .extra import Extra
from .technique import Technique

class InstancePhysicsScene(DaeObject):
    def __init__(self,pscene=None, url=None, sid=None, name=None, extras=None, xmlnode=None):
        self.pscene = pscene
        self.url = url
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_kinematics_model()
            self.save()

    @staticmethod
    def load( collada, localscope, node ):
        pscene=None
        url = node.get('url')
        if url.startswith('#'):
            pscene = collada.physics_scenes.get(url[1:])
        sid = node.get('sid')
        name = node.get('name')
        extras = Extra.loadextras(collada, node)
        return InstancePhysicsScene(pscene,url,sid,name,extras,xmlnode=node)
    
    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.kscene is not None:
            self.xmlnode.set('url','#'+self.kscene.id)
        else:
            self.xmlnode.set('url',self.url)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)

class PhysicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <physics_scene> tag"""
    def __init__(self, collada, id, name, physics_models=None, instance_physics_models=None, asset = None, technique_common=None, xmlnode=None):
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
        self.collada = collada
        self.id = id
        self.name = name
        self.physics_models = []
        if physics_models is not None:
            self.physics_models = physics_models
        self.instance_physics_models = []
        if instance_physics_models is not None:
            self.instance_physics_models = instance_physics_models
        
        """The collada instance this is part of"""
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the scene node."""
            self.extras = Extra.loadextras(self.collada, self.xmlnode)
            self.techniques = Technique.loadtechniques(self.collada, self.xmlnode)
        else:
            self.extras = []
            self.techniques = []
            self.xmlnode = E.physics_scene()
            self.save()
        
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        name = node.get('name')
        physics_models=[]
        instance_physics_models=[]
        technique_common = None
        asset = None
        for subnode in node:
            if subnode.tag == tag('instance_physics_model'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'): # inside this doc, so search for it
                        kmodel = collada.physics_models.get(url[1:])
                        if kmodel is None:
                            raise DaeBrokenRefError('physics_model %s not found in library'%url)

                        physics_models.append(kmodel)
                    else:
                        instance_physics_models.append(InstancePhysicsModel(url,xmlnode=subnode)) # external reference
            elif subnode.tag == tag('asset'):
                asset = Asset.load(collada, {}, subnode)
            elif subnode.tag == tag('technique_common'):
                technique_common = subnode
            elif subnode.tag == tag('instance_force_field'):
                pass
        return PhysicsScene(collada, id, name, physics_models, instance_physics_models, asset, technique_common, xmlnode=node)

    def save(self):
        Extra.saveextras(self.xmlnode,self.extras)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common()
            self.xmlnode.append(technique_common)
        else:
            #technique_common.clear()
            pass
        
        oldnodes = self.xmlnode.findall(tag('instance_physics_models'))
        for node in oldnodes:
            self.xmlnode.remove(oldnode)
        for model in self.instance_physics_models:
            self.xmlnode.append(model.xmlnode)
        for pm in self.physics_models:
            ipm = E.instance_physics_model()
            ipm.set('url','#'+pm.id)
            self.xmlnode.append(ipm)

        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.name)
