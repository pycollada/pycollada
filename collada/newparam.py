####################################################################
#                                                                  #
# THIS FILE IS PART OF THE pycollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE pycollada SOURCE CODE IS (C) COPYRIGHT 2011                  #
# by Jeff Terrace, Rosen Diankov, and contributors                 #
#                                                                  #
####################################################################
from .common import DaeObject, E, tag, CommonFloat, CommonInt, CommonBool
from .sidref import SIDREF

class NewParam(DaeObject):
    def __init__(self, sid, value, xmlnode=None):
        self.sid = sid
        self.value = value
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.newparam()
            self.save(0)
    
    @staticmethod
    def load( collada, localscope, scoped_node_for_sids, node ):
        sid = node.get('sid')
        value = None
        for child in node.getchildren():
            if child.tag == tag('float'):
                value = CommonFloat.load(collada, {}, child)
                break
            elif child.tag == tag('int'):
                value = CommonInt.load(collada, {}, child)
                break
            elif child.tag == tag('bool'):
                value = CommonBool.load(collada, {}, child)
                break
            elif child.tag == tag('SIDREF'):
                value = SIDREF.load(collada, localscope, scoped_node_for_sids, child)
                break
        newparam = NewParam(sid, value, node)
        collada.addSid(sid, newparam)
        return newparam
    
    @staticmethod
    def loadnewparams(collada, xmlnode):
        """returns all newparams from children of node"""
        newparam_nodes = xmlnode.findall(tag('newparam')) or []
        return [NewParam.load(collada, {}, None, newparam_node) for newparam_node in newparam_nodes]

    def save(self,recurse=True):
        """Saves the info back to :attr:`xmlnode`"""
        if self.sid is not None:
            self.xmlnode.set('sid',self.sid)
        for oldnode in self.xmlnode.getchildren():
            self.xmlnode.remove(oldnode)
        if self.value is not None:
            if recurse:
                # depending on the value type, this might be a pycollada object or not
                self.value.save(recurse)
            self.xmlnode.append(self.value.xmlnode)
            
    def getchildren(self):
        return [self.value] if self.value is not None else []

