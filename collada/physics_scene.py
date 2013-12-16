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

from .common import DaeObject, E, tag, save_attribute, save_child_object
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .xmlutil import UnquoteSafe
from .physics_model import InstancePhysicsModel
from .extra import Extra
from .technique import Technique
from .asset import Asset

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
            self.xmlnode = E.instance_physics_scene()
            self.save()

    @staticmethod
    def load( collada, localscope, node ):
        pscene=None
        # according to http://www.w3.org/TR/2001/WD-charmod-20010126/#sec-URIs, URIs in XML are always %-encoded, therefore
        url=UnquoteSafe(node.get('url'))
        if url.startswith('#'):
            pscene = collada.physics_scenes.get(url[1:])
        sid = node.get('sid')
        name = node.get('name')
        extras = Extra.loadextras(collada, node)
        inst_pscene = InstancePhysicsScene(pscene,url,sid,name,extras,xmlnode=node)
        collada.addSid(sid, inst_pscene)
        return inst_pscene

    def getchildren(self):
        return self.extras
    
    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras,recurse)
        # prioritize saving the url rather than self.kscene in order to account for external references
        if self.url is not None:
            self.xmlnode.set('url',self.url)
        elif self.pscene is not None:
            self.xmlnode.set('url','#'+self.pscene.id)
        else:
            self.xmlnode.attrib.pop('url',None)
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'name',self.name)
        
class PhysicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <physics_scene> tag"""
    def __init__(self, id, name, instance_physics_models=None, asset = None, technique_common=None, techniques=None, extras=None, xmlnode=None):
        """Create a scene

        :param str id:
          A unique string identifier for the scene
        :param list nodes:
          A list of type :class:`collada.scene.Node` representing the nodes in the scene
        :param xmlnode:
          When loaded, the xmlnode it comes from

        """
        self.id = id
        self.name = name
        self.asset = asset
        self.instance_physics_models = []
        if instance_physics_models is not None:
            self.instance_physics_models = instance_physics_models
        self.extras = []
        if extras is not None:
            self.extras = extras
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the scene node."""
        else:
            self.xmlnode = E.physics_scene()
            self.save(0)
        
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
                instance_physics_models.append(InstancePhysicsModel.load(collada,{},subnode))
            elif subnode.tag == tag('asset'):
                asset = Asset.load(collada, {}, subnode)
            elif subnode.tag == tag('technique_common'):
                technique_common = subnode
            elif subnode.tag == tag('instance_force_field'):
                pass
        extras = Extra.loadextras(collada, node)
        techniques = Technique.loadtechniques(collada, node)
        pscene = PhysicsScene(id, name, instance_physics_models, asset, technique_common, techniques, extras, xmlnode=node)
        collada.addId(id, pscene)
        return pscene

    # FIXME: skips technique_common
    def getchildren(self):
        return self.instance_physics_models + self.extras + self.techniques

    def save(self,recurse=True):
        Extra.saveextras(self.xmlnode,self.extras,recurse)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common()
            self.xmlnode.append(technique_common)
        technique_common.clear()
        
        oldnodes = self.xmlnode.findall(tag('instance_physics_model'))
        for node in oldnodes:
            self.xmlnode.remove(node)
        for model in self.instance_physics_models:
            if recurse:
                model.save()
            self.xmlnode.append(model.xmlnode)

        save_child_object(self.xmlnode, tag('asset'), self.asset, recurse)
        save_attribute(self.xmlnode,'id',self.id)
        save_attribute(self.xmlnode,'name',self.name)
