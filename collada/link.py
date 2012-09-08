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

class Link(DaeObject):
    """A class containing the data coming from a COLLADA <link> tag"""
    def __init__(self, collada, sid, name, attachments=None, xmlnode=None):
        self.collada = collada
        self.sid = sid
        self.name = name

        self.attachments = []
        if attachments is not None:
            self.attachments = attachments

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.link()
            if len(self.sid) > 0: self.xmlnode.set("sid", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    @staticmethod
    def load( collada, localscope, node ):
        sid = node.get("sid") or ""
        name = node.get("name") or ""     
        node = Link(collada, sid, name, xmlnode=node )
        return node

    def save(self):
        self.xmlnode.set('sid', self.sid)
        self.xmlnode.set('name', self.name)
