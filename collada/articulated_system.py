####################################################################
#                                                                  #
# THIS FILE IS PART OF THE pycollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE pycollada SOURCE CODE IS (C) COPYRIGHT 2011                  #
# by Jeff Terrace, Rosen Diankov, and contributors                 #
#                                                                  #
####################################################################
"""Contains objects for representing an articulated system."""
import copy
from .common import DaeObject, E, tag, save_attribute, CommonParam, CommonFloat, CommonBool, CommonInt
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .xmlutil import UnquoteSafe
from .kinematics_model import InstanceKinematicsModel
from .extra import Extra
from .technique import Technique
from .asset import Asset
from .newparam import NewParam

class InstanceArticulatedSystem(DaeObject):
    def __init__(self,asystem=None, url=None, sid=None, name=None, newparams=None, setparams=None, extras=None, xmlnode=None):
        """
        :param newparams: list of xml nodes for <newparam> tag
        :param setparams: list of xml nodes for <setparam> tag
        """
        self.asystem = asystem
        self.url = url
        self.sid = sid
        self.name = name
        self.newparams = []
        if newparams is not None:
            self.newparams = newparams
        self.setparams = []
        if setparams is not None:
            self.setparams = setparams
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
        # according to http://www.w3.org/TR/2001/WD-charmod-20010126/#sec-URIs, URIs in XML are always %-encoded, therefore
        url=UnquoteSafe(node.get('url'))
        sid=node.get('sid')
        name=node.get('name')
        newparams = NewParam.loadnewparams(collada, node)
        setparams = node.findall(tag('sewparam'))
        if url is not None:
            if url.startswith('#'): # inside this doc, so search for it
                asystem = collada.articulated_systems.get(url[1:])
                # don't raise an exception if asystem is None
        extras = Extra.loadextras(collada, node)
        inst_asystem = InstanceArticulatedSystem(asystem, url, sid, name, newparams, setparams, extras, xmlnode=node)
        collada.addSid(sid, inst_asystem)
        return inst_asystem

    # FIXME: this leaves out setparams (because we don't have a class for them yet) and binds (because we don't track them)
    def getchildren(self):
        return self.newparams + self.extras

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        # prioritize saving the url rather than self.kscene in order to account for external references
        if self.url is not None:
            self.xmlnode.set('url',self.url)
        elif self.asystem is not None:
            self.xmlnode.set('url','#'+self.asystem.id)
        else:
            self.xmlnode.attrib.pop('url',None)
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'name',self.name)
        for oldnode in self.xmlnode.findall(tag('newparam')) + self.xmlnode.findall(tag('setparam')):
            self.xmlnode.remove(oldnode)
        for newparam in self.newparams:
            if recurse:
                newparam.save(recurse)
            self.xmlnode.append(newparam.xmlnode)
        for setparam in self.setparams:
            self.xmlnode.append(setparam)

class KinematicsAxisInfo(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics>/<axis_info> tag
    """
    def __init__(self, sid=None, name=None, axis=None, active=None, locked=None, index=None, limits_min=None, limits_max=None, newparams=None, formulas=None, xmlnode=None):
        self.sid = sid
        self.name = name
        self.axis = axis
        self.active = active
        self.locked = locked
        self.index = index
        self.limits_min = limits_min
        self.limits_max = limits_max
        self.newparams = []
        if newparams is not None:
            self.newparams = newparams
        self.formulas = []
        if formulas is not None:
            self.formulas = formulas
            
        if xmlnode is not None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.axis_info()
            self.save(0)
            
    @staticmethod
    def load(collada, localscope, node):
        sid = node.get('sid')
        active=None
        locked=None
        index=None
        limits_min=None
        limits_max=None
        newparams = NewParam.loadnewparams(collada, node)
        formulas=[]
        for subnode in node:
            if subnode.tag == tag('active'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        active = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('bool'):
                        active = CommonBool.load(collada, {}, subnode[0])
            elif subnode.tag == tag('locked'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        locked = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('bool'):
                        locked = CommonBool.load(collada, {}, subnode[0])
            elif subnode.tag == tag('index'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        index = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('int'):
                        index = CommonInt.load(collada, {}, subnode[0])
            elif subnode.tag == tag('limits'):
                xmlmin = subnode.find(tag('min'))
                if xmlmin is not None:
                    if len(xmlmin) == 1:
                        if xmlmin[0].tag == tag('param'):
                            limits_min = CommonParam.load(collada, {}, xmlmin[0])
                        elif xmlmin[0].tag == tag('float'):
                            limits_min = CommonFloat.load(collada, {}, xmlmin[0])            
                xmlmax = subnode.find(tag('max'))
                if xmlmax is not None:
                    if len(xmlmax) == 1:
                        if xmlmax[0].tag == tag('param'):
                            limits_max = CommonParam.load(collada, {}, xmlmax[0])
                        elif xmlmax[0].tag == tag('float'):
                            limits_max = CommonFloat.load(collada, {}, xmlmax[0])
                            
        axisinfo = KinematicsAxisInfo(sid, node.get('name'), node.get('axis'), active, locked, index, limits_min, limits_max, newparams, formulas, xmlnode=node)
        collada.addSid(sid, axisinfo)
        return axisinfo
    
    def getchildren(self):
        return self.newparams
    
    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'name',self.name)
        save_attribute(self.xmlnode,'axis',self.axis)

        xmlnode = self.xmlnode
        for previouschild in xmlnode.findall(tag('active')):
            xmlnode.remove(previouschild)
        if self.active is not None:
            if recurse:
                self.active.save(recurse)
            xmlactive = E.active()
            xmlactive.append(self.active.xmlnode)
            self.xmlnode.append(xmlactive)

        for previouschild in xmlnode.findall(tag('locked')):
            xmlnode.remove(previouschild)
        if self.locked is not None:
            if recurse:
                self.locked.save(recurse)
            xmllocked = E.locked()
            xmllocked.append(self.locked.xmlnode)
            self.xmlnode.append(xmllocked)

        for previouschild in xmlnode.findall(tag('index')):
            xmlnode.remove(previouschild)
        if self.index is not None:
            if recurse:
                self.index.save(recurse)
            xmlindex = E.index()
            xmlindex.append(self.index.xmlnode)
            self.xmlnode.append(xmlindex)

        for previouschild in xmlnode.findall(tag('limits')):
            xmlnode.remove(previouschild)
        if self.limits_min is not None or self.limits_max is not None:
            if recurse:
                if self.limits_min is not None:
                    self.limits_min.save(recurse)
                if self.limits_max is not None:
                    self.limits_max.save(recurse)
            xmllimits = E.limits()
            if self.limits_min is not None:
                xmllimits_min = E.min()
                xmllimits_min.append(self.limits_min.xmlnode)
                xmllimits.append(xmllimits_min)
            if self.limits_max is not None:
                xmllimits_max = E.max()
                xmllimits_max.append(self.limits_max.xmlnode)
                xmllimits.append(xmllimits_max)
            self.xmlnode.append(xmllimits)
            
        for oldnode in self.xmlnode.findall(tag('newparam')):
            self.xmlnode.remove(oldnode)
        for newparam in self.newparams:
            if recurse:
                newparam.save(recurse)
            self.xmlnode.append(newparam.xmlnode)
    
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
                        axisinfos.append(KinematicsAxisInfo.load(collada, {}, subsubnode))
        extras = Extra.loadextras(collada, node)
        techniques = Technique.loadtechniques(collada,node)
        return Kinematics(instance_kinematics_models,axisinfos,techniques, extras, xmlnode=node)

    def getchildren(self):
        return self.instance_kinematics_models + self.techniques + self.extras + self.axisinfos
    
    def save(self,recurse=True):
        """Saves the kinematics node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        for oldnode in self.xmlnode.findall(tag('instance_kinematics_model')):
            self.xmlnode.remove(oldnode)
        for ikmodel in self.instance_kinematics_models:
            if recurse:
                ikmodel.save(recurse)
            self.xmlnode.append(ikmodel.xmlnode)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common()
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for axisinfo in self.axisinfos:
            if recurse:
                axisinfo.save(recurse)
            technique_common.append(axisinfo.xmlnode)

class MotionAxisInfo(DaeObject):
    """A class containing the data coming from a COLLADA <motion>/<axis_info> tag
    :param newparams: list of xml nodes for <newparam> tag
    :param setparams: list of xml nodes for <setparam> tag
    """
    def __init__(self, sid=None, name=None, axis=None, speed=None, acceleration=None, deceleration=None, jerk=None, newparams=None, setparams=None, xmlnode=None):
        self.sid = sid
        self.name = name
        self.axis = axis
        self.speed = speed
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.jerk = jerk
        self.newparams = []
        if newparams is not None:
            self.newparams = newparams
        self.setparams = []
        if setparams is not None:
            self.setparams = setparams
        
        if xmlnode is not None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.axis_info()
            self.save(0)
        
    @staticmethod
    def load(collada, localscope, node):
        sid = node.get('sid')
        speed=None
        acceleration=None
        deceleration=None
        jerk=None
        newparams = NewParam.loadnewparams(collada, node)
        setparams = node.findall(tag('sewparam'))
        for subnode in node:
            if subnode.tag == tag('speed'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        speed = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('float'):
                        speed = CommonFloat.load(collada, {}, subnode[0])
            elif subnode.tag == tag('acceleration'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        acceleration = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('float'):
                        acceleration = CommonFloat.load(collada, {}, subnode[0])
            elif subnode.tag == tag('deceleration'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        deceleration = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('float'):
                        deceleration = CommonFloat.load(collada, {}, subnode[0])
            elif subnode.tag == tag('jerk'):
                if len(subnode) == 1:
                    if subnode[0].tag == tag('param'):
                        jerk = CommonParam.load(collada, {}, subnode[0])
                    elif subnode[0].tag == tag('float'):
                        jerk = CommonFloat.load(collada, {}, subnode[0])
        axisinfo = MotionAxisInfo(sid, node.get('name'), node.get('axis'), speed, acceleration, deceleration, jerk, newparams, setparams, xmlnode=node)
        collada.addSid(sid, axisinfo)
        return axisinfo
    
    # FIXME: this leaves out setparams (because we don't have a class for them yet) and binds (because we don't track them)
    def getchildren(self):
        return self.newparams
    
    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'name',self.name)
        save_attribute(self.xmlnode,'axis',self.axis)
        
        for previouschild in xmlnode.findall(tag('speed')):
            xmlnode.remove(previouschild)
        if self.speed is not None:
            if recurse:
                self.speed.save(recurse)
            xmlspeed = E.speed()
            xmlspeed.append(self.speed.xmlnode)
            self.xmlnode.append(xmlspeed)

        for previouschild in xmlnode.findall(tag('acceleration')):
            xmlnode.remove(previouschild)
        if self.acceleration is not None:
            if recurse:
                self.acceleration.save(recurse)
            xmlacceleration = E.acceleration()
            xmlacceleration.append(self.acceleration.xmlnode)
            self.xmlnode.append(xmlacceleration)

        for previouschild in xmlnode.findall(tag('deceleration')):
            xmlnode.remove(previouschild)
        if self.deceleration is not None:
            if recurse:
                self.deceleration.save(recurse)
            xmldeceleration = E.deceleration()
            xmldeceleration.append(self.deceleration.xmlnode)
            self.xmlnode.append(xmldeceleration)

        for previouschild in xmlnode.findall(tag('jerk')):
            xmlnode.remove(previouschild)
        if self.jerk is not None:
            if recurse:
                self.jerk.save(recurse)
            xmljerk = E.jerk()
            xmljerk.append(self.jerk.xmlnode)
            self.xmlnode.append(xmljerk)
            
        for oldnode in self.xmlnode.findall(tag('newparam')) + self.xmlnode.findall(tag('setparam')):
            self.xmlnode.remove(oldnode)
        for newparam in self.newparams:
            if recurse:
                newparam.save(recurse)
            self.xmlnode.append(newparam.xmlnode)
        for setparam in self.setparams:
            self.xmlnode.append(setparam)    
    

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
                        axisinfos.append(MotionAxisInfo.load(collada, {}, subsubnode))
        extras = Extra.loadextras(collada, node)
        return Motion(instance_articulated_system,axisinfos,extras, xmlnode=node)

    def getchildren(self):
        iasystems = [ self.instance_articulated_system ] if self.instance_articulated_system is not None else []
        return self.extras + iasystems

    def save(self,recurse=True):
        """Saves the motion node back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        ias = self.xmlnode.find(tag('instance_articulated_system'))
        if ias is not None:
            self.xmlnode.remove(ias)
        elif self.instance_articulated_system is not None:
            if recurse:
                self.instance_articulated_system.save(recurse)
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
        asystem = ArticulatedSystem(id, name, kinematics, motion, asset, extras, xmlnode=node )
        collada.addId(id, asystem)
        return asystem

    def getchildren(self):
        children = []
        for c in [self.kinematics, self.motion, self.asset]:
            if c:
                children.append(c)
        return children + self.extras

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.kinematics is not None:
            if recurse:
                self.kinematics.save(recurse)
            node = self.xmlnode.find(tag('kinematics'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.kinematics.xmlnode)
        if self.motion is not None:
            if recurse:
                self.motion.save(recurse)
            node = self.xmlnode.find(tag('motion'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.motion.xmlnode)
        save_attribute(self.xmlnode,'id',self.id)
        save_attribute(self.xmlnode,'name',self.name)
