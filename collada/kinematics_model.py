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

class InstanceKinematicsModel(object):
    def __init__(self,url, sid='', name='', xmlnode=None):
        self.url = url
        self.sid = sid
        self.name = name
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.instance_kinematics_model()
            self.save()
    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
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
    def __init__(self, collada, id, name, links=None, joints=None, formulas=None, xmlnode=None):
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
        self.collada = collada
        """The :class:`collada.Collada` object this geometry belongs to"""

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

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.kinematics_model()
            for link in self.links:
                self.xmlnode.append(link.node)
            for joint in self.joints:
                self.xmlnode.append(joint.node)
            for formula in self.formulas:
                self.xmlnode.append(formula.node)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id") or ""
        name = node.get("name") or ""
        links=[]
        joints=[]
        formulas=[]
        node = KinematicsModel(collada, id, name, links=links, joints=joints, formulas=formulas, xmlnode=node )
        return node
