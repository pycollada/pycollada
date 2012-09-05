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
"""Contains objects for representing a kinematics scene."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
from .kinematics_model import InstanceKinematicsModel
from .articulated_system import InstanceArticulatedSystem

class KinematicsScene(DaeObject):
    """A class containing the data coming from a COLLADA <kinematics_scene> tag"""
    def __init__( self, collada, id, name, kinematics_models=None, instance_kinematics_models=None, articulated_systems=None, instance_articulated_systems=None, xmlnode=None):
        self.id = id
        """The unique string identifier for the scene"""
        
        self.name = name
        """The text string naming the scene"""
        
        self.collada = collada
        """The collada instance this is part of"""

        self.kinematics_models = []
        if kinematics_models is not None:
            self.kinematics_models = kinematics_models
        self.instance_kinematics_models = []
        if instance_kinematics_models is not None:
            self.instance_kinematics_models = instance_kinematics_models
        self.articulated_systems = []
        if articulated_systems is not None:
            self.articulated_systems = articulated_systems
        self.instance_articulated_systems = []
        if instance_articulated_systems is not None:
            self.instance_articulated_systems = instance_articulated_systems
        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.kinematics_scene()
            for model in self.kinematics_models + self.instance_kinematics_models + self.articulated_systems + self.instance_articulated_systems:
                self.xmlnode.append(model.xmlnode)
            if len(self.id) > 0: self.xmlnode.set("id", self.id)
            if len(self.name) > 0: self.xmlnode.set("name", self.name)
            
    @staticmethod
    def load( collada, node ):
        id = node.get('id')
        name = node.get('name')
        kinematics_models = []
        instance_kinematics_models = []
        articulated_systems = []
        instance_articulated_systems = []
        for subnode in node:
            if subnode.tag == tag('instance_kinematics_model'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'): # inside this doc, so search for it
                        kmodel = collada.kinematics_models.get(url[1:])
                        if kmodel is None:
                            raise DaeBrokenRefError('kinematics_model %s not found in library'%url)

                        kinematics_models.append(kmodel)
                    else:
                        instance_kinematics_models.append(InstanceKinematicsModel(url,xmlnode=subnode)) # external reference
            elif subnode.tag == tag('instance_articulated_system'):
                url=subnode.get('url')
                if url is not None:
                    if url.startswith('#'): # inside this doc, so search for it
                        asystem = collada.articulated_systems.get(url[1:])
                        if asystem is None:
                            raise DaeBrokenRefError('articulated_system %s not found in library'%url)
                        
                        articulated_systems.append(asystem)
                    else:
                        instance_articulated_systems.append(InstanceArticulatedSystem(url,xmlnode=subnode)) # external reference
        return KinematicsScene(id, name, kinematics_models, instance_kinematics_models, articulated_systems, instance_articulated_systems)
