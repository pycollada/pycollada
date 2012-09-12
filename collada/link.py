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
"""Contains objects for representing a kinematics link."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from transform import TranslateTransform, RotateTransform

class Attachment(DaeObject):
    """A class containing the data coming from a COLLADA <attachment_full> tag"""
    def __init__(self, attachmenttype=None, joint=None, link=None, transformnodes=None, xmlnode=None):
        """
        :param attachmenttype: one of full, start, or end
        """
        self.attachmenttype=attachmenttype
        self.joint=joint
        self.link = link
        self.transformnodes = []
        if transformnodes is not None:
            self.transformnodes = transformnodes
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            if attachmenttype == 'full':
                self.xmlnode = E.attachment_full()
            elif attachmenttype == 'start':
                self.xmlnode = E.attachment_start()
            elif attachmenttype == 'end':
                self.xmlnode = E.attachment_end()
            self.save(0)
        
    @staticmethod
    def load( collada, localscope, node, attachmenttype ):
        joint = node.get("joint")
        link = None
        transformnodes=[]
        for subnode in node:
            if subnode.tag == tag('link'):
                link = Link.load(collada, localscope, subnode)
            elif subnode.tag == tag('translate'):
                transformnodes.append(TranslateTransform.load(collada,subnode))
            elif subnode.tag == tag('rotate'):
                transformnodes.append(RotateTransform.load(collada,subnode))
        node = Attachment(attachmenttype, joint, link, transformnodes, xmlnode=node)
        return node

    def save(self,recurse=-1):
        self.xmlnode.clear()
        self.xmlnode.set('joint', self.joint)
        for node in self.transformnodes:
            if recurse:
                node.save()
            self.xmlnode.append(node.xmlnode)
        if self.link is not None:
            if recurse:
                self.link.save()
            self.xmlnode.append(self.link.xmlnode)
            
class Link(DaeObject):
    """A class containing the data coming from a COLLADA <link> tag"""
    def __init__(self, sid, name, transformnodes=None, attachments=None, xmlnode=None):
        self.sid = sid
        self.name = name
        
        self.transformnodes = []
        if transformnodes is not None:
            self.transformnodes = transformnodes

        self.attachments = []
        if attachments is not None:
            self.attachments = attachments
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.link()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        sid = node.get("sid")
        name = node.get("name")
        transformnodes=[]
        attachments=[]
        for subnode in node:
            if subnode.tag == tag('attachment_full'):
                attachments.append(Attachment.load(collada, localscope, subnode, 'full'))
            elif subnode.tag == tag('attachment_start'):
                attachments.append(Attachment.load(collada, localscope, subnode, 'start'))
            elif subnode.tag == tag('attachment_end'):
                attachments.append(Attachment.load(collada, localscope, subnode, 'end'))
            elif subnode.tag == tag('translate'):
                transformnodes.append(TranslateTransform.load(collada,subnode))
            elif subnode.tag == tag('rotate'):
                transformnodes.append(RotateTransform.load(collada,subnode))
        node = Link(sid, name, transformnodes, attachments, xmlnode=node )
        return node

    def save(self,recurse=-1):
        self.xmlnode.clear()
        for node in self.transformnodes:
            if recurse:
                node.save()
            self.xmlnode.append(node.xmlnode)
        for node in self.attachments:
            if recurse:
                node.save()
            self.xmlnode.append(node.xmlnode)

        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
