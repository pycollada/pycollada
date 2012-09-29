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
#         param = node.find(tag('param'))
#         sidref = node.find(tag('SIDREF'))
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
            self.save(0)
    @staticmethod
    def load( collada, localscope, node ):
        noderef = node.get('node')
        scenenode=None
        if noderef is not None:
            pass
        param = node.find(tag('param'))
        sidref = node.find(tag('SIDREF'))
        return BindKinematicsModel(scenenode, noderef, param,sidref,xmlnode=node)

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        if self.noderef is not None:
            self.xmlnode.set('node',self.noderef)
        elif self.scenenode is not None:
            self.xmlnode.set('node','#'+self.scenenode.id)
        else:
            self.xmlnode.attrib.pop('node',None)
        param = self.xmlnode.find(tag('param'))
        if param is not None:
            self.xmlnode.remove(param)
        if self.param is not None:
            self.xmlnode.append(self.param)
        sidref = self.xmlnode.find(tag('sidref'))
        if sidref is not None:
            self.xmlnode.remove(sidref)
        if self.sidref is not None:
            self.xmlnode.append(self.sidref)

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
            self.save(0)
    @staticmethod
    def load( collada, localscope, node ):
        targetref = node.get('target')
        scenenode=None
        if targetref is not None:
            pass
        axis = node.find(tag('axis'))
        value = node.find(tag('value'))
        return BindJointAxis(scenenode, targetref,axis, value,xmlnode=node)

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        if self.targetref is not None:
            self.xmlnode.set('target',self.targetref)
        elif self.scenenode is not None:
            self.xmlnode.set('target','#'+self.scenenode.id)
        else:
            self.xmlnode.attrib.pop('target',None)
        axis = self.xmlnode.find(tag('axis'))
        if axis is not None:
            self.xmlnode.remove(axis)
        if self.axis is not None:
            self.xmlnode.append(self.axis)
        value = self.xmlnode.find(tag('value'))
        if value is not None:
            self.xmlnode.remove(value)
        if self.value is not None:
            self.xmlnode.append(self.value)
    
class InstanceKinematicsScene(DaeObject):
    def __init__(self,kscene=None, url=None, sid=None, name=None, asset=None, extras=None, bind_kinematics_models=None, bind_joint_axes=None, xmlnode=None):
        self.kscene = kscene
        self.url = url
        self.sid = sid
        self.name = name
        self.extras = []
        self.asset = asset
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
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        kscene=None
        url = node.get('url')
        if url.startswith('#'):
            kscene = collada.kinematics_scenes.get(url[1:])
        sid = node.get('sid')
        name = node.get('name')
        if name is not None and kscene is not None:
            kscene.name = name
        asset=None
        extras=[]
        bind_kinematics_models=[]
        bind_joint_axes=[]
        for subnode in node:
            if subnode.tag == tag('asset'):
                asset = Asset.load(collada, {}, subnode)
            elif subnode.tag == tag('bind_kinematics_model'):
                bind_kinematics_models.append(BindKinematicsModel.load(collada,localscope,subnode))
            elif subnode.tag == tag('bind_joint_axis'):
                bind_joint_axes.append(BindJointAxis.load(collada,localscope,subnode))
        extras = Extra.loadextras(collada, node)
        return InstanceKinematicsScene(kscene,url,sid,name,asset,extras,bind_kinematics_models, bind_joint_axes, xmlnode=node)
    
    def save(self, recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.kscene is not None:
            self.xmlnode.set('url','#'+self.kscene.id)
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
        asset = self.xmlnode.find(tag('asset'))
        if asset is not None:
            self.xmlnode.remove(asset)
        if self.asset is not None:
            if recurse:
                self.asset.save(recurse)
            self.xmlnode.append(self.asset.xmlnode)
        oldnodes = self.xmlnode.findall('bind_kinematics_model') + self.xmlnode.findall('bind_joint_axis')
        for oldnode in oldnodes:
            self.xmlnode.remove(oldnode)
        for node in self.bind_kinematics_models + self.bind_joint_axes:
            if recurse:
                node.save(recurse)
            self.xmlnode.append(node.xmlnode)
            
class KinematicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_scene> tag"""
    def __init__( self, id, name, instance_kinematics_models=None, instance_articulated_systems=None, extras=None, xmlnode=None):
        self.id = id
        """The unique string identifier for the scene"""
        
        self.name = name
        """The text string naming the scene"""

        self.instance_kinematics_models = []
        if instance_kinematics_models is not None:
            self.instance_kinematics_models = instance_kinematics_models
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
            self.save(0)
            
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        name = node.get('name')
        instance_kinematics_models = []
        instance_articulated_systems = []
        for subnode in node:
            if subnode.tag == tag('instance_kinematics_model'):
                instance_kinematics_models.append(InstanceKinematicsModel.load(collada, {}, subnode))
            elif subnode.tag == tag('instance_articulated_system'):
                instance_articulated_systems.append(InstanceArticulatedSystem.load(collada, {}, subnode))
        extras = Extra.loadextras(collada, node)
        return KinematicsScene(id, name, instance_kinematics_models, instance_articulated_systems, extras, xmlnode=node)

    def save(self,recurse=True):
        if self.id is not None:
            self.xmlnode.set('id',self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
            
        Extra.saveextras(self.xmlnode,self.extras)
        oldnodes = self.xmlnode.findall(tag('instance_kinematics_model'))+self.xmlnode.findall(tag('instance_articulated_system'))
        for node in oldnodes:
            self.xmlnode.remove(node)
        for model in self.instance_kinematics_models + self.instance_articulated_systems:
            if recurse:
                model.save(recurse)
            self.xmlnode.append(model.xmlnode)
