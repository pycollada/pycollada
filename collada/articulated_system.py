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

"""Contains objects for representing an articulated system."""

import numpy

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class Kinematics(object):
    """A class containing the data coming from a COLLADA <kinematics> tag"""
    def __init__(self, collada, instance_kinematics_model_urls,axisinfo,xmlnode=None):
        self.instance_kinematics_model_urls = []
        self.kinematics_models = []
        for url in instance_kinematics_model_urls:
            if 0:#url.startswith('#'): # inside this doc, so search for it
                kmodel = collada.kinematics_models.get(url[1:])
                if kmodel is None:
                    raise DaeBrokenRefError('kinematics_model %s not found in library'%url)
                self.kinematics_models.append(kmodel)
            else:
                self.instance_kinematics_model_urls.append(url) # external
        self.axisinfo = axisinfo
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.kinematics(*self.axisinfo)
            self.xmlnode.append(E.technique_common())
        self.xmlnode = xmlnode
        
    @staticmethod
    def load(collada, node):
        instance_kinematics_model_urls = []
        axisinfo = []
        for subnode in node:
            if subnode.tag == tag('instance_kinematics_model'):
                url=subnode.get('url')
                if url is not None:
                    instance_kinematics_model_urls.append(url)
            elif subnode.tag == tag('technique_common'):
                for subsubnode in subnode:
                    if subsubnode == tag('axis_info'):
                        axisinfo.append(subsubnode)
                        # parse <limits>?
        return Kinematics(collada, instance_kinematics_model_urls,axisinfo,xmlnode=node)

    def save(self):
        """Saves the kinematics node back to :attr:`xmlnode`"""
        self.xmlnode.set('url', "#%s" % self.geometry.id)

class Motion(object):
    """A class containing the data coming from a COLLADA <motion> tag"""
    def __init__(self, collada, instance_articulated_system_url,axisinfo,xmlnode=None):
        self.instance_articulated_system_url = None
        self.articulated_system = None
        if instance_articulated_system_url.startswith('#'):
            self.articulated_system = collada.articulated_systems.get(instance_articulated_system_url[1:])
            if self.articulated_system is None:
                raise DaeBrokenRefError('articulated_system %s not found in library'%url)
            
        else:
            self.instance_articulated_system_url = instance_articulated_system_url # external reference
        self.axisinfo = axisinfo
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.motion(*self.axisinfo)
            self.xmlnode.append(E.technique_common())
        
    @staticmethod
    def load(collada, node):
        instance_articulated_system_url = None
        axisinfo = []
        for subnode in node:
            if subnode.tag == tag('instance_articulated_system'):
                url=subnode.get('url')
                if url is not None:
                    instance_articulated_system_url = url
            elif subnode.tag == tag('technique_common'):
                for subsubnode in subnode:
                    if subsubnode == tag('axis_info'):
                        axisinfo.append(subsubnode)
                        # parse <speed>, <acceleration>, <deceleration>, <jerk>?
        return Motion(collada, instance_articulated_system_url,axisinfo,xmlnode=node)

class ArticulatedSystem(DaeObject):
    """A class containing the data coming from a COLLADA <articulated_system> tag"""
    def __init__(self, collada, id, name, kinematics=None, motion=None, xmlnode=None):
        """Create a geometry instance

          :param collada.Collada collada:
            The collada object this geometry belongs to
          :param str id:
            A unique string identifier for the geometry
          :param str name:
            A text string naming the geometry
          :param kinematics: xml element for <kinematics>
          :param motion: xml element for <motion>
          :param xmlnode:
            When loaded, the xmlnode it comes from.

        """
        self.collada = collada
        """The :class:`collada.Collada` object this geometry belongs to"""

        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.kinematics = kinematics

        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            if self.kinematics is not None:
                self.xmlnode = E.articulated_system(self.kinematics)
            else:
                self.xmlnode = E.articulated_system(self.motion)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get("id") or ""
        name = node.get("name") or ""
        motion = None
        kinematics = None
        kinematicsnode = node.find(tag('kinematics'))
        if kinematicsnode is None:
            motionnode = node.find(tag('motion'))
            if motionnode is None:
                raise DaeUnsupportedError('artiuclated_system needs to have kinematics or motion node')

            motion = Motion.load(collada, motionnode)
        else:
            kinematics = Kinematics.load(collada, kinematicsnode)
        node = ArticulatedSystem(collada, id, name, kinematics, motion, xmlnode=node )
        return node

    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        if self.kinematics is not None:
            self.kinematics.save()
            node = self.xmlnode.find(tag('kinematics'))
            if node is not None:
                node.remove()
            self.xmlnode.append(self.kinematics)
        if self.motion is not None:
            self.motion.save()
            node = self.xmlnode.find(tag('motion'))
            if node is not None:
                node.remove()
            self.xmlnode.append(self.motion)
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.name)
