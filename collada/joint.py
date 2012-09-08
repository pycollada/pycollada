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
"""Contains objects for representing a kinematics joint."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .extra import Extra

class Joint(DaeObject):
    """A class containing the data coming from a COLLADA <joint> tag"""
    def __init__(self, collada, id, sid, name, attachments=None, xmlnode=None):
        self.collada = collada
        self.id = id
        self.sid = sid
        self.name = name

        self.attachments = []
        if attachments is not None:
            self.attachments = attachments

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
            self.extras = Extra.loadextras(self.collada, self.xmlnode)
        else:
            self.extras = []
            self.xmlnode = E.joint()
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.sid) > 0: self.xmlnode.set("sid", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id") or ""
        sid = node.get("sid") or ""
        name = node.get("name") or ""     
        node = Joint(collada, id, sid, name, xmlnode=node )
        return node

    def save(self):
        Extra.saveextras(self.xmlnode,self.extras)
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('sid', self.sid)
        self.xmlnode.set('name', self.name)
