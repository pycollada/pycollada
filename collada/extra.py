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
"""Contains <extra> definitions."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .asset import Asset
from .technique import Technique

class Extra(DaeObject):
    """Represents extra information in a scene, as defined in a collada <extra> tag."""
        
    def __init__(self, id=None, name=None, type=None, asset=None, technique_common=None, techniques=None, xmlnode=None):
        """Create a <extra>

        :param str id:
          A unique string identifier for the object
        :param str name:
            A text string naming the object
        :param str type:
            A text string for type of object
        :param str asset: Asset object
        :param technique_common: lxml node whose tag is technique_common
        :param list techniques:
        A list of Technique objects
        """
        self.id = id
        self.name = name
        self.type = type
        self.asset = asset
        self.technique_common = technique_common
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.extra()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        id=node.get('id')
        name = node.get('name')
        type = node.get('type')
        asset=None
        technique_common=None
        techniques=[]
        for subnode in node:
            if subnode.tag == tag('asset'):
                asset=Asset.load(collada,localscope,subnode)
            elif subnode.tag == tag('technique_common'):
                technique_common = subnode
            elif subnode.tag == tag('technique'):
                techniques.append(Technique.load(collada,localscope,subnode))
        return Extra(id,name,type,asset,technique_common,techniques,xmlnode=node)

    def save(self,recurse=True):
        if self.id is not None:
            self.xmlnode.set('id', self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
        if self.type is not None:
            self.xmlnode.set('type',self.type)
        else:
            self.xmlnode.attrib.pop('type',None)
        if self.asset is not None:
            if recurse:
                self.asset.save()
            node = self.xmlnode.find(tag('asset'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.asset)
        if self.technique_common is not None:
            node = self.xmlnode.find(tag('technique_common'))
            if node is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.technique_common)
        for oldnode in self.xmlnode.findall(tag('technique')):
            self.xmlnode.remove(oldnode)
        for tec in self.techniques:
            if recurse:
                tec.save()
            self.xmlnode.append(tec.xmlnode)

    @staticmethod
    def loadextras(collada, xmlnode):
        """returns all extras from children of node"""
        extras = []
        for subnode in xmlnode:
            if subnode.tag == tag('extra'):
                extras.append(Extra.load(collada, {}, subnode))
        return extras

    @staticmethod
    def saveextras(xmlnode,extras):
        """saves extras to children of node"""
        # remove all <extra> tags and add the new ones
        for oldnode in xmlnode.findall(tag('extra')):
            xmlnode.remove(oldnode)
        for extra in extras:
            extra.save()
            xmlnode.append(extra.xmlnode)

