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
    def __init__(self, collada, id=None, name=None, type=None, asset=None, technique_common=None, techniques=None, xmlnode=None):
        """Create a <extra>

        :param collada:
          The collada instance this is part of
        :param str id:
          A unique string identifier for the scene
        :param list techniques:
        A list of Technique objects
        :param technique_common: lxml node whose tag is technique_common
        """
        self.collada=collada
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
            self.save()

    @staticmethod
    def load( collada, localscope, node ):
        pass

    def save(self):
        if self.id is not None:
            self.xmlnode.set('id',self.sid)
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
            self.asset.save()
            node = self.xmlnode.find(tag('asset'))
            if not is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.asset)
        if self.technique_common is not None:
            node = self.xmlnode.find(tag('technique_common'))
            if not is not None:
                self.xmlnode.remove(node)
            self.xmlnode.append(self.technique_common)
        for oldnode in self.xmlnode.findall(tag('technique')):
            self.xmlnode.remove(oldnode)
        for tec in self.techniques:
            tec.save()
            self.xmlnode.append(tec.xmlnode)
