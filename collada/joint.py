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
    def __init__(self, id, sid, name, extras=None, xmlnode=None):
        self.id = id
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras
            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.joint()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id")
        sid = node.get("sid")
        name = node.get("name")
        extras = Extra.loadextras(collada, node)
        node = Joint(id, sid, name, extras, xmlnode=node )
        return node

    def save(self, recurse=-1):
        Extra.saveextras(self.xmlnode,self.extras)
        if self.id is not None:
            self.xmlnode.set('id',self.id)
        else:
            self.xmlnode.attrib.pop('id',None)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)
