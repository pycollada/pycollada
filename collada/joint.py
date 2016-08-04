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

def _loadValuesOfPrismaticOrRevolute( collada, localscope, node ):
    sid = node.get('sid')
    axis_node = node.find(tag('axis'))
    if axis_node is not None:
        axis_values = [float(s) for s in axis_node.text.split()]
    else:
        axis_values = None
    min_limit = None
    max_limit = None
    limits_node = node.find(tag('limits'))
    if limits_node is None:
        min_node = limits_node.find(tag('min'))
        if min_node is not None:
            min_limit = float(min_node.text)
        max_node = limits_node.find(tag('max'))
        if max_node is not None:
            max_limit = float(max_node.text)
    return (sid, axis_values, min_limit, max_limit)

class Prismatic(DaeObject):
    """A class containing the data coming from a COLLADA <prismatic> tag"""
    def __init__(self, sid, axis=None, min_limit=None, max_limit=None, xmlnode=None):
        """Create <prismatic>
        
        """
        self.sid = sid
        self.axis = axis
        self.min_limit = min_limit
        self.max_limit = max_limit

        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.prismatic()
            self.save(0)

    # NOTE: ignoring sids for axis, min, and max
    def getchildren(self):
        return []
    
    # NOTE: ignoring sids for axis, min, and max
    @staticmethod
    def load( collada, localscope, node ):
        (sid, axis_values, min_limit, max_limit) = _loadValuesOfPrismaticOrRevolute(collada, localscope, node)
        node = Prismatic(sid, axis=axis_values, min_limit=min_limit, max_limit=max_limit, xmlnode=node)
        collada.addSid(sid, node)
        return node
    
    def save(self,recurse=True):
        self.xmlnode.clear()
        self.xmlnode.set('sid', self.sid)
        if self.axis is not None:
            xmlaxis = E.axis()
            xmlaxis.text = ' '.join(['%.15f'%f for f in self.axis])
            self.xmlnode.append(xmlaxis)
        
        if self.min_limit is not None and self.max_limit is not None:
            xmllimits = E.limits()
            xmlmin = E.min()
            xmlmin.text = '%.15f'%self.min_limit
            xmllimits.append(xmlmin)
            xmlmax = E.max()
            xmlmax.text = '%.15f'%self.max_limit
            xmllimits.append(xmlmax)
            self.xmlnode.append(xmllimits)
        
class Revolute(DaeObject):
    """A class containing the data coming from a COLLADA <revolute> tag"""
    def __init__(self, sid, axis=None, min_limit=None, max_limit=None, xmlnode=None):
        """Create <revolute>

        FIXME
        """
        self.sid = sid
        self.axis = axis
        self.min_limit = min_limit
        self.max_limit = max_limit

        if xmlnode != None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.revolute()
            self.save(0)

    # NOTE: ignoring sids for axis, min, and max
    def getchildren(self):
        return []

    # NOTE: ignoring sids for axis, min, and max
    @staticmethod
    def load( collada, localscope, node ):
        (sid, axis_text, min_text, max_text) = _loadValuesOfPrismaticOrRevolute(collada, localscope, node)
        node = Revolute(sid, axis=axis_text, min_limit=min_text, max_limit=max_text, xmlnode=node)
        collada.addSid(sid, node)
        return node
    
    def save(self,recurse=True):
        self.xmlnode.clear()
        self.xmlnode.set('sid', self.sid)
        if self.axis is not None:
            xmlaxis = E.axis()
            xmlaxis.text = ' '.join(['%.15f'%f for f in self.axis])
            self.xmlnode.append(xmlaxis)
        
        if self.min_limit is not None and self.max_limit is not None:
            xmllimits = E.limits()
            xmlmin = E.min()
            xmlmin.text = '%.15f'%self.min_limit
            xmllimits.append(xmlmin)
            xmlmax = E.max()
            xmlmax.text = '%.15f'%self.max_limit
            xmllimits.append(xmlmax)
            self.xmlnode.append(xmllimits)
    
class Joint(DaeObject):
    """A class containing the data coming from a COLLADA <joint> tag"""
    def __init__(self, id, sid, name, prismatics=None, revolutes=None, extras=None, xmlnode=None):
        """Create <joint>
        
        :param str id:
          A unique string identifier for the object
        :param str sid:
            A text string for sid the object
        :param str name:
            A text string naming the object
        :param list extras: list of Extra
        """
        self.id = id
        self.sid = sid
        self.name = name
        self.extras = []
        if extras is not None:
            self.extras = extras

        self.prismatics = []
        if prismatics is not None:
            self.prismatics = prismatics

        self.revolutes = []
        if revolutes is not None:
            self.revolutes = revolutes
            
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
        prismatic_nodes = node.findall(tag('prismatic'))
        prismatics = [Prismatic.load(collada, localscope, pnode) for pnode in prismatic_nodes]
        revolute_nodes = node.findall(tag('revolute'))
        revolutes = [Revolute.load(collada, localscope, rnode) for rnode in revolute_nodes]
        extras = Extra.loadextras(collada, node)
        node = Joint(id, sid, name, prismatics=prismatics, revolutes=revolutes, extras=extras, xmlnode=node)
        collada.addId(id, node)
        collada.addSid(sid, node)
        return node

    def getchildren(self):
        return self.extras + self.prismatics + self.revolutes

    def save(self, recurse=True):
        self.xmlnode.clear()
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
        
        for prismatic in self.prismatics:
            if recurse:
                prismatic.save()
            self.xmlnode.append(prismatic.xmlnode)
        
        for revolute in self.revolutes:
            if recurse:
                revolute.save()
            self.xmlnode.append(revolute.xmlnode)
        
