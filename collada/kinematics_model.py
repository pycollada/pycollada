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
"""Contains objects for representing a kinematics model."""

import copy
from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .extra import Extra
from .technique import Technique
from .asset import Asset
from .link import Link
from .joint import Joint

class InstanceKinematicsModel(DaeObject):
    def __init__(self,kmodel=None, url=None, sid=None, name=None, extras = None, xmlnode=None):
        self.kmodel = kmodel
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
        kmodel=None
        url=node.get('url')
        sid=node.get('sid')
        name=node.get('name')
        if url is not None:
            if url.startswith('#'): # inside this doc, so search for it
                kmodel = collada.kinematics_models.get(url[1:])
                if kmodel is None:
                    raise DaeBrokenRefError('kinematics_model %s not found in library'%url)
                
                if name is not None:
                    kmodel = copy.copy(kmodel)
                    kmodel.name = name
                
        extras = Extra.loadextras(collada, node)
        return InstanceKinematicsModel(kmodel, url, sid, name, extras, xmlnode=node)
    
    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        if self.kmodel is not None and self.kmodel.id is not None:
            self.xmlnode.set('url','#'+self.kmodel.id)
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
            
class KinematicsModel(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_model> tag"""
    def __init__(self, id, name, links=None, joints=None, formulas=None, asset = None, techniques=None, extras=None, xmlnode=None):
        """Create a kinematics_model instance

          :param collada.Collada collada:
            The collada object this geometry belongs to
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
            for link in self.links:
                self.xmlnode.append(link.xmlnode)
            for joint in self.joints:
                self.xmlnode.append(joint.xmlnode)
            for formula in self.formulas:
                self.xmlnode.append(formula.xmlnode)
            if self.asset is not None:
                self.xmlnode.append(self.asset.xmlnode)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

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
                        pass
                    elif subnode2.tag == tag('joint'):
                        joints.append(Joint.load(collada,localscope, subnode2))
                    elif subnode2.tag == tag('instance_joint'):
                        pass
                        #joints.append(Joint.load(collada,localscope, subnode2))
            elif subnode.tag == tag('asset'):
                asset = Asset.load(collada, localscope, subnode)
        techniques = Technique.loadtechniques(collada, node)
        extras = Extra.loadextras(collada, node)
        node = KinematicsModel(id, name, links, joints, formulas, asset, techniques, extras, xmlnode=node )
        return node

    def save(self):
        Extra.saveextras(self.xmlnode,self.extras)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common(tag('technique_common'))
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for obj in self.links + self.joints + self.formulas:
            obj.save()
            technique_common.append(obj.xmlnode)
        asset = self.xmlnode.find(tag('asset'))
        if asset is not None:
            self.xmlnode.remove(asset)
        if self.asset is not None:
            self.asset.save()
            self.xmlnode.append(self.asset.xmlnode)
        if self.id is not None:
            self.xmlnode.set('id',self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
