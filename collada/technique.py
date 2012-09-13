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
"""Contains <technique> definitions"""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class Technique(DaeObject):
    def __init__(self, profile, xmlns=None, xmlnode=None):
        self.profile = profile
        self.xmlns = xmlns
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.technique()
            self.save(0)

    def save(self,recurse=-1):
        """Saves the info back to :attr:`xmlnode`"""
        self.xmlnode.set('profile',self.profile)
        if self.xmlns is not None:
            self.xmlnode.set('xmlns',self.xmlns)
        else:
            self.xmlnode.attrib.pop('xmlns',None)

    @staticmethod
    def load( collada, localscope, node ):
        profile = node.get('profile')
        xmlns = node.get('xmlns')
        return Technique(profile, xmlns, xmlnode=node)

    @staticmethod
    def loadtechniques(collada, xmlnode):
        """returns all techniques from children of node"""
        techniques = []
        for subnode in xmlnode:
            if subnode.tag == tag('technique'):
                techniques.append(Technique.load(collada, {}, subnode))
        return techniques

    @staticmethod
    def savetechniques(xmlnode,techniques):
        """saves techniques to children of node"""
        # remove all <technique> tags and add the new ones
        for oldnode in xmlnode.findall(tag('technique')):
            xmlnode.remove(oldnode)
        for technique in techniques:
            technique.save()
            xmlnode.append(technique.xmlnode)
