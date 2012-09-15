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
"""Contains objects for representing an articulated system."""
import copy
from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .kinematics_model import InstanceKinematicsModel
from .extra import Extra
from .technique import Technique
from .asset import Asset

class InstanceArticulatedSystem(DaeObject):
    def __init__(self,asystem=None, url=None, sid=None, name=None, extras=None, xmlnode=None):
        self.asystem = asystem
        self.url = url
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_articulated_system()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        asystem=None
        url=node.get('url')
        sid=node.get('sid')
        name=node.get('name')
        if url is not None:
            if url.startswith('#'): # inside this doc, so search for it
                asystem = collada.articulated_systems.get(url[1:])
                if asystem is None:
                    raise DaeBrokenRefError('articulated_system %s not found in library'%url)
                if name is not None:
                    asystem = copy.copy(asystem)
                    asystem.name = name
        extras = Extra.loadextras(collada, node)
        return InstanceArticulatedSystem(asystem, url, sid, name, extras, xmlnode=node)

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.asystem is not None:
            self.xmlnode.set('url','#'+self.asystem.id)
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

class Kinematics(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics> tag"""
    def __init__(self, instance_kinematics_models=None,axisinfos=None,techniques=None, extras=None, xmlnode=None):
        """Create a <kinematics>

        :param list instance_kinematics_models: a InstanceKinematicsModel
        :param list axisinfos: list of xmlnodes
        :param list techniques: list of Technique
        :param list extras: list of Extra
        :param xmlnode:
        When loaded, the xmlnode it comes from
        """
        self.extras = []
        if extras is not None:
            self.extras = extras
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques
            
        self.instance_kinematics_models = []
        if instance_kinematics_models is not None:
            self.instance_kinematics_models = instance_kinematics_models
        self.axisinfos = []
        if axisinfos is not None:
            self.axisinfos = axisinfos
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.kinematics(*self.axisinfos)
            self.save(0)
        
    @staticmethod
    def load(collada, localscope, node):
        instance_kinematics_models = []
        axisinfos = []
        for subnode in node:
            if subnode.tag == tag('instance_kinematics_model'):
                instance_kinematics_models.append(InstanceKinematicsModel.load(collada, {}, subnode)) # external reference
            elif subnode.tag == tag('technique_common'):
                for subsubnode in subnode:
                    if subsubnode.tag == tag('axis_info'):
                        axisinfos.append(subsubnode)
                        # parse <limits>?
        extras = Extra.loadextras(collada, node)
        techniques = Technique.loadtechniques(collada,node)
        return Kinematics(instance_kinematics_models,axisinfos,techniques, extras,xmlnode=node)

    def save(self,recurse=True):
        """Saves the kinematics node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        for oldnode in self.xmlnode.findall(tag('instance_kinematics_model')):
            self.xmlnode.remove(oldnode)
        for ikmodel in self.instance_kinematics_models:
            if recurse:
                ikmodel.save()
            self.xmlnode.append(ikmodel.xmlnode)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common()
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for axisinfo in self.axisinfos:
            technique_common.append(axisinfo)        

class Motion(DaeObject):
    """A class containing the data coming from a COLLADA <motion> tag"""
    def __init__(self, instance_articulated_system=None,axisinfos=None,extras=None,xmlnode=None):
        """Create a <motion>

        :param instance_articulated_system: a InstanceArticulatedSystem
        :param list axisinfos: list of xmlnodes
        :param list techniques: list of Technique
        :param list extras: list of Extra
        :param xmlnode:
        When loaded, the xmlnode it comes from
        """
        self.instance_articulated_system = instance_articulated_system
        self.axisinfos = []
        if axisinfos is not None:
            self.axisinfos = axisinfos
        self.extras = []
        if extras is not None:
            self.extras = extras
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.motion(*self.axisinfos)
            self.save(0)
        
    @staticmethod
    def load(collada, localscope, node):
        instance_articulated_system = None
        axisinfos = []
        for subnode in node:
            if subnode.tag == tag('instance_articulated_system'):
                instance_articulated_system = InstanceArticulatedSystem.load(collada, {}, subnode)
            elif subnode.tag == tag('technique_common'):
                for subsubnode in subnode:
                    if subsubnode.tag == tag('axis_info'):
                        axisinfos.append(subsubnode)
                        # parse <speed>, <acceleration>, <deceleration>, <jerk>?
        extras = Extra.loadextras(collada, node)
        return Motion(instance_articulated_system,axisinfos,extras, xmlnode=node)

    def save(self,recurse=True):
        """Saves the motion node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        ias = self.xmlnode.find(tag('instance_articulated_system'))
        if ias is None:
            self.xmlnode.remove(ias)
        elif self.instance_articulated_system is not None:
            if recurse:
                self.instance_articulated_system.save()
            self.xmlnode.append(self.instance_articulated_system.xmlnode)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common()
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for axisinfo in self.axisinfos:
            technique_common.append(axisinfo)

class ArticulatedSystem(DaeObject):
    """A class containing the data coming from a COLLADA <articulated_system> tag"""
    def __init__(self, id, name, kinematics=None, motion=None, asset=None, extras=None, xmlnode=None):
        """Create a articulated_system instance

          :param str id:
            A unique string identifier for the geometry
          :param str name:
            A text string naming the geometry
          :param kinematics: Kinematics object
          :param motion: Motion object
          :param asset: Asset object
          :param list extras: list of Extra
          :param xmlnode:
            When loaded, the xmlnode it comes from.

        """
        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.kinematics = kinematics
        self.motion = motion
        self.asset = asset
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.articulated_system()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id")
        name = node.get("name")
        motion = None
        kinematics = None
        asset = None
        kinematicsnode = node.find(tag('kinematics'))
        if kinematicsnode is None:
            motionnode = node.find(tag('motion'))
            if motionnode is None:
                raise DaeUnsupportedError('artiuclated_system needs to have kinematics or motion node')
            
            motion = Motion.load(collada, localscope, motionnode)
        else:
            kinematics = Kinematics.load(collada, localscope, kinematicsnode)
        assetnode = node.find(tag('asset'))
        if assetnode is not None:
            asset = Asset.load(collada,localscope,assetnode)
        extras = Extra.loadextras(collada, node)
        node = ArticulatedSystem(id, name, kinematics, motion, asset, extras, xmlnode=node )
        return node

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.kinematics is not None:
            if recurse:
                self.kinematics.save()
            node = self.xmlnode.find(tag('kinematics'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.kinematics.xmlnode)
        if self.motion is not None:
            if recurse:
                self.motion.save()
            node = self.xmlnode.find(tag('motion'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.motion.xmlnode)
        if self.id is not None:
            self.xmlnode.set('id',self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
        
