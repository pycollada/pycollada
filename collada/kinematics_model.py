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

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .extra import Extra
from .technique import Technique
from .asset import Asset
from .link import Link
from .joint import Joint

class InstanceKinematicsModel(DaeObject):
    def __init__(self,url, sid=None, name=None, xmlnode=None):
        self.url = url
        self.sid = sid
        self.name = name
        if xmlnode is not None:
            self.xmlnode = xmlnode
            self.extras = Extra.loadextras(self.collada, self.xmlnode)
        else:
            self.extras = []
            self.xmlnode = E.instance_kinematics_model()
            self.save()
    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('url',self.url)
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
        id = node.get("id") or ""
        name = node.get("name") or ""
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
                asset = Asset.load(collada, localscope, node)
        techniques = Technique.loadtechniques(collada, node)
        extras = Extra.loadextras(collada, node)
        node = KinematicsModel(id, name, links, joints, formulas, asset, techniques, extras, xmlnode=node )
        return node

    def save(self):
        Extra.saveextras(self.xmlnode,self.extras)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is not None:
            self.xmlnode.remove(technique_common)
        if self.technique_common is not None:
            self.xmlnode.append(self.technique_common)
        for obj in self.links + self.joints + self.formulas:
            obj.save()
            self.xmlnode.append(obj.xmlnode)
        asset = self.xmlnode.find('asset')
        if asset is not None:
            self.xmlnode.remove(asset)
        if self.asset is not None:
            self.asset.save()
            self.xmlnode.append(self.asset.xmlnode)
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.name)
