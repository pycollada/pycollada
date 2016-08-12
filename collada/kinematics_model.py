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
"""Contains objects for representing a kinematics model."""

import copy
from .common import DaeObject, E, tag, save_attribute, save_child_object
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .xmlutil import UnquoteSafe
from .extra import Extra
from .technique import Technique
from .asset import Asset
from .link import Link
from .joint import Joint
from .formula import Formula
from .newparam import NewParam

class InstanceKinematicsModel(DaeObject):
    def __init__(self,kmodel=None, url=None, sid=None, name=None, extras = None, newparams=None, setparams=None, xmlnode=None):
        """
        :param newparams: list of xml nodes for <newparam> tag
        :param setparams: list of xml nodes for <setparam> tag
        """
        self.kmodel = kmodel
        self.url = url
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras
        
        self.newparams = newparams if newparams else []
        self.setparams = []
        if setparams is not None:
            self.setparams = setparams
        
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_kinematics_model()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        kmodel=None
        # according to http://www.w3.org/TR/2001/WD-charmod-20010126/#sec-URIs, URIs in XML are always %-encoded, therefore
        url=UnquoteSafe(node.get('url'))
        sid=node.get('sid')
        name=node.get('name')
        if url is not None:
            if url.startswith('#'): # inside this doc, so search for it
                kmodel = collada.kinematics_models.get(url[1:])
                # don't raise an exception if asystem is None
        extras = Extra.loadextras(collada, node)
        newparams = NewParam.loadnewparams(collada, node)
        setparams = node.findall(tag('sewparam'))
        inst_kmodel = InstanceKinematicsModel(kmodel, url, sid, name, extras, newparams, setparams, xmlnode=node)
        collada.addSid(sid, inst_kmodel)
        return inst_kmodel

    def getchildren(self):
        return self.extras + self.newparams
    
    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        # prioritize saving the url rather than self.kscene in order to account for external references
        if self.url is not None:
            self.xmlnode.set('url',self.url)
        elif self.kmodel is not None and self.kmodel.id is not None:
            self.xmlnode.set('url','#'+self.kmodel.id)
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
    
class KinematicsModel(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_model> tag"""
    def __init__(self, id, name, links=None, joints=None, formulas=None, asset = None, techniques=None, extras=None, xmlnode=None):
        """Create a kinematics_model instance

          :param str id:
            A unique string identifier for the geometry
          :param str name:
            A text string naming the geometry
          :param list links: list of links
          :param list joints: list of joints
          :param list formulas: list of formulas
          :param xmlnode:
            When loaded, the xmlnode it comes from.

        """
        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.links = []
        if links is not None:
            self.links = links

        self.joints = []
        if joints is not None:
            self.joints = joints

        self.formulas = []
        if formulas is not None:
            self.formulas = formulas

        self.asset = asset
        self.extras = []
        if extras is not None:
            self.extras = extras
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.kinematics_model()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id")
        name = node.get("name")
        links=[]
        joints=[]
        formulas=[]
        asset = None
        for subnode in node:
            if subnode.tag == tag('technique_common'):
                for subnode2 in subnode:
                    if subnode2.tag == tag('link'):
                        links.append(Link.load(collada, localscope, subnode2))
                    elif subnode2.tag == tag('formula'):
                        formulas.append(Formula.load(collada, localscope, subnode2))
                    elif subnode2.tag == tag('joint'):
                        joints.append(Joint.load(collada,localscope, subnode2))
                    elif subnode2.tag == tag('instance_joint'):
                        pass
                        #joints.append(Joint.load(collada,localscope, subnode2))

            elif subnode.tag == tag('asset'):
                asset = Asset.load(collada, localscope, subnode)
        techniques = Technique.loadtechniques(collada, node)
        extras = Extra.loadextras(collada, node)
        kmodel = KinematicsModel(id, name, links, joints, formulas, asset, techniques, extras, xmlnode=node )
        collada.addId(id, kmodel)
        return kmodel

    def getchildren(self):
        assets = [ self.asset ] if self.asset is not None else []
        return self.links + self.joints + self.formulas + self.techniques + self.extras + assets

    def save(self,recurse=True):
        Extra.saveextras(self.xmlnode,self.extras)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common(tag('technique_common'))
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for obj in self.links + self.joints + self.formulas:
            if recurse:
                obj.save(recurse)
            technique_common.append(obj.xmlnode)
        
        save_child_object(self.xmlnode, tag('asset'), self.asset, recurse)
        save_attribute(self.xmlnode,'id',self.id)
        save_attribute(self.xmlnode,'name',self.name)
