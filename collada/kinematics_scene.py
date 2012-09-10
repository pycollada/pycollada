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

import copy
from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .asset import Asset
from .extra import Extra
from .articulated_system import InstanceArticulatedSystem
from .kinematics_model import InstanceKinematicsModel

# class CommonSidrefOrParam(DaeObject):
#     def __init__(self,param=None,sidref=None,xmlnode=None):
#         self.param=param
#         self.sidref=sidref
#         if xmlnode is not None:
#             self.xmlnode = xmlnode
#         else:
#             self.xmlnode = E.bind_kinematics_model()
#             self.save()
#     @staticmethod
#     def load( collada, localscope, node ):
#         param = node.find('param')
#         sidref = node.find('SIDREF')
#         return CommonSidrefOrParam(param,sidref,xmlnode)

class BindKinematicsModel(DaeObject):
    def __init__(self,scenenode,noderef, param=None,sidref=None,xmlnode=None):
        self.scenenode=scenenode
        self.noderef=noderef
        self.param=param
        self.sidref=sidref
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.bind_kinematics_model()
            self.save()
    @staticmethod
    def load( collada, localscope, node ):
        noderef = node.get('node')
        scenenode=None
        if noderef is not None:
            pass
        param = node.find('param')
        sidref = node.find('SIDREF')
        return BindKinematicsModel(scenenode, noderef, param,sidref,xmlnode=node)

class BindJointAxis(DaeObject):
    def __init__(self,scenenode,targetref, axis=None,value=None,xmlnode=None):
        self.scenenode=scenenode
        self.targetref=targetref
        self.axis=axis
        self.value=value
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.bind_joint_axis()
            self.save()
    @staticmethod
    def load( collada, localscope, node ):
        targetref = node.get('target')
        scenenode=None
        if targetref is not None:
            pass
        axis = node.find('axis')
        value = node.find('value')
        return BindJointAxis(scenenode, targetref,axis, value,xmlnode=node)
    
class InstanceKinematicsScene(DaeObject):
    def __init__(self,kscene=None, url=None, sid=None, name=None, asset=None, extras=None, bind_kinematics_models=None, bind_joint_axes=None, xmlnode=None):
        self.kscene = kscene
        self.url = url
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras
        self.bind_kinematics_models = []
        if bind_kinematics_models is not None:
            self.bind_kinematics_models = bind_kinematics_models
        self.bind_joint_axes = []
        if bind_joint_axes is not None:
            self.bind_joint_axes = bind_joint_axes
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_kinematics_model()
            self.save()

    @staticmethod
    def load( collada, localscope, node ):
        kscene=None
        url = node.get('url')
        if url.startswith('#'):
            kscene = collada.kinematics_scenes.get(url[1:])
        sid = node.get('sid')
        name = node.get('name')
        asset=None
        extras=[]
        bind_kinematics_models=[]
        bind_joint_axes=[]
        for subnode in node:
            if subnode.tag == tag('asset'):
                asset = Asset.load(collada, {}, subnode)
            elif subnode.tag == tag('bind_kinematics_model'):
                bind_kinematics_models.append(BindKinematicsModel.load(collada,localscope,node))
            elif subnode.tag == tag('bind_joint_axis'):
                bind_joint_axes.append(BindJointAxis.load(collada,localscope,node))
        extras = Extra.loadextras(collada, node)
        return InstanceKinematicsScene(kscene,url,sid,name,asset,extras,bind_kinematics_models, bind_joint_axes, xmlnode=node)
    
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
        asset = self.xmlnode.find('asset')
        if asset is not None:
            self.xmlnode.remove(asset)
        if self.asset is not None:
            self.asset.save()
            self.xmlnode.append(self.asset.xmlnode)
        oldnodes = self.xmlnode.findall('bind_kinematics_model') + self.xmlnode.findall('bind_joint_axis')
        for oldnode in oldnodes:
            self.xmlnode.remove(oldnode)
        for node in self.bind_kinematics_models + self.bind_joint_axes:
            node.save()
            self.xmlnode.append(node)
            
class KinematicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_scene> tag"""
    def __init__( self, id, name, kinematics_models=None, instance_kinematics_models=None, articulated_systems=None, instance_articulated_systems=None, extras=None, xmlnode=None):
        self.id = id
        """The unique string identifier for the scene"""
        
        self.name = name
        """The text string naming the scene"""

        self.kinematics_models = []
        if kinematics_models is not None:
            self.kinematics_models = kinematics_models
        self.instance_kinematics_models = []
        if instance_kinematics_models is not None:
            self.instance_kinematics_models = instance_kinematics_models
        self.articulated_systems = []
        if articulated_systems is not None:
            self.articulated_systems = articulated_systems
        self.instance_articulated_systems = []
        if instance_articulated_systems is not None:
            self.instance_articulated_systems = instance_articulated_systems
        self.extras = []
        if extras is not None:
            self.extras = extras
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.kinematics_scene()
            for model in self.instance_kinematics_models + self.instance_articulated_systems:
                self.xmlnode.append(model.xmlnode)
            for km in self.kinematics_models:
                ikm = E.instance_kinematics_model()
                ikm.set('url','#'+ikm.id)
                self.xmlnode.append(ikm)
            for asystem in self.articulated_systems:
                ias = E.instance_articulated_system()
                ias.set('url','#'+asystem.id)
            self.xmlnode.append(ias)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)
            
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        name = node.get('name')
        kinematics_models = []
        instance_kinematics_models = []
        articulated_systems = []
        instance_articulated_systems = []
        for subnode in node:
            if subnode.tag == tag('instance_kinematics_model'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'): # inside this doc, so search for it
                        kmodel = collada.kinematics_models.get(url[1:])
                        if kmodel is None:
                            raise DaeBrokenRefError('kinematics_model %s not found in library'%url)

                        kmodel = copy.copy(kmodel)
                        if subnode.get('name') is not None:
                            kmodel.name = subnode.get('name')
                        kinematics_models.append(kmodel)
                    else:
                        instance_kinematics_models.append(InstanceKinematicsModel(url,xmlnode=subnode)) # external reference
            elif subnode.tag == tag('instance_articulated_system'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'): # inside this doc, so search for it
                        asystem = collada.articulated_systems.get(url[1:])
                        if asystem is None:
                            raise DaeBrokenRefError('articulated_system %s not found in library'%url)

                        asystem = copy.copy(asystem)
                        if subnode.get('name') is not None:
                            asystem.name = subnode.get('name')
                        articulated_systems.append(asystem)
                    else:
                        instance_articulated_systems.append(InstanceArticulatedSystem(url,xmlnode=subnode)) # external reference
        extras = Extra.loadextras(collada, node)
        return KinematicsScene(id, name, kinematics_models, instance_kinematics_models, articulated_systems, instance_articulated_systems, extras, xmlnode=node)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.name)
        self.extras = Extra.loadextras(self.collada, self.xmlnode)
        oldnodes = self.xmlnode.findall(tag('instance_kinematics_models')+tag('instance_articulated_systems'))
        for node in oldnodes:
            self.xmlnode.remove(oldnode)
        for model in self.instance_kinematics_models + self.instance_articulated_systems:
            self.xmlnode.append(model.xmlnode)
        for km in self.kinematics_models:
            ikm = E.instance_kinematics_model()
            ikm.set('url','#'+km.id)
            if km.name is not None:
                ikm.set('name',km.name)
            self.xmlnode.append(ikm)
        for asystem in self.articulated_systems:
            ias = E.instance_articulated_system()
            ias.set('url','#'+asystem.id)
            if asystem.name is not None:
                ias.set('name',asystem.name)
            self.xmlnode.append(ias)
