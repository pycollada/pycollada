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

"""Contains objects for representing a physics model."""

import numpy

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .extra import Extra
from .technique import Technique

class InstanceRigidBody(object):
    def __init__(self,body, target, sid=None, name=None, techniques=None, extras=None, xmlnode=None):
        self.body = body
        self.target = target
        self.name = name
        self.sid = sid
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques
        self.extras = []
        if extras is not None:
            self.extras = extras

        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_articulated_system()
            self.save(0)

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        Extra.savetechniques(self.xmlnode,self.techniques)
        self.xmlnode.set('body',self.body)
        self.xmlnode.set('target',self.target)
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        else:
            self.xmlnode.attrib.pop('sid',None)
        if self.name is not None:
            self.xmlnode.set('name',self.name)
        else:
            self.xmlnode.attrib.pop('name',None)


    @staticmethod
    def load( collada, localscope, node ):
        body=node.get('body')
        target=node.get('target')
        sid=node.get('sid')
        name=node.get('name')
        extras = Extra.loadextras(collada, node)
        techniques = Technique.loadtechniques(collada, node)
        return InstanceRigidBody(body, target, sid, name, techniques, extras, xmlnode)
