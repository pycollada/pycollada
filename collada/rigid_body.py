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

from .common import DaeObject, E, tag, save_attribute, save_child_object
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .extra import Extra
from .technique import Technique

class InstanceRigidBody(object):
    def __init__(self,rigid_body, body, target, sid=None, name=None, techniques=None, extras=None, xmlnode=None):
        self.rigid_body = rigid_body
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

    @staticmethod
    def load( collada, localscope, node ):
        body=node.get('body')
        rigid_body = None
        target=node.get('target')
        sid=node.get('sid')
        name=node.get('name')
        extras = Extra.loadextras(collada, node)
        techniques = Technique.loadtechniques(collada, node)
        return InstanceRigidBody(rigid_body, body, target, sid, name, techniques, extras, xmlnode)

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        Extra.saveextras(self.xmlnode,self.extras)
        Extra.savetechniques(self.xmlnode,self.techniques)
        self.xmlnode.set('body',self.body)
        self.xmlnode.set('target',self.target)
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'name',self.name)

class RigidBody(DaeObject):
    """A class containing the data coming from a COLLADA <rigid_body> tag"""
    def __init__(self, sid, id=None, name=None, dynamic=None, mass=None, mass_frame=None, inertia=None, physics_materials=None, shapes=None, techniques=None, extras=None, xmlnode=None):
        """Create a kinematics_model instance

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
        self.sid = sid
        self.id = id
        """The unique string identifier for the geometry"""

        self.name = name
        """The text string naming the geometry"""

        self.dynamic = dynamic
        self.mass = mass
        self.mass_frame = mass_frame
        self.inertia = inertia
        
        self.physics_materials = []
        if physics_materials is not None:
            self.physics_materials = physics_materials

        self.shapes = []
        if shapes is not None:
            self.shapes = shapes

        self.extras = []
        if extras is not None:
            self.extras = extras
        self.techniques = []
        if techniques is not None:
            self.techniques = techniques            
        if xmlnode != None:
            self.xmlnode = xmlnode
            """ElementTree representation of the geometry."""
        else:
            self.xmlnode = E.rigid_body()
            self.save(0)

    @staticmethod
    def load( collada, localscope, node ):
        sid = node.get("sid")
        id = node.get("id")
        name = node.get("name")
        
        dynamic=None
        mass=None
        mass_frame=None
        inertia=None
        physics_materials=[]
        shapes=[]
        for subnode in node:
            if subnode.tag == tag('technique_common'):
                for subnode2 in subnode:
                    if subnode2.tag == tag('dynamic'):
                        dynamic = subnode2
                    elif subnode2.tag == tag('mass'):
                        mass = subnode2
                    elif subnode2.tag == tag('mass_frame'):
                        mass_frame = subnode2
                    elif subnode2.tag == tag('inertia'):
                        inertia = subnode2
                    elif subnode2.tag == tag('physics_material'):
                        physics_materials.append(subnode2)
                    elif subnode2.tag == tag('shape'):
                        shapes.append(subnode2)
        techniques = Technique.loadtechniques(collada, node)
        extras = Extra.loadextras(collada, node)
        return RigidBody(sid, id, name, dynamic, mass, mass_frame, inertia, physics_materials, shapes, techniques, extras, xmlnode=node)

    def save(self,recurse=True):
        Extra.saveextras(self.xmlnode,self.extras)
        Technique.savetechniques(self.xmlnode,self.techniques)
        technique_common = self.xmlnode.find(tag('technique_common'))
        if technique_common is None:
            technique_common = E.technique_common(tag('technique_common'))
            self.xmlnode.append(technique_common)
        technique_common.clear()
        for obj in self.physics_materials + self.shapes:
            # for now, obj is an xml node
            technique_common.append(obj)
            #if recurse:
            #    obj.save(recurse)
            #technique_common.append(obj.xmlnode)
        #save_child_object(technique_common, tag('dynamic'), self.dynamic, recurse)
        #save_child_object(technique_common, tag('mass'), self.mass, recurse)
        #save_child_object(technique_common, tag('mass_frame'), self.mass_frame, recurse)
        #save_child_object(technique_common, tag('inertia'), self.inertia, recurse)
        save_attribute(self.xmlnode,'sid',self.sid)
        save_attribute(self.xmlnode,'id',self.id)
        save_attribute(self.xmlnode,'name',self.name)
