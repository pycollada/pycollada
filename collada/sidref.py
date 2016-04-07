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
import copy
from .common import DaeObject, E

# FIXME: only works when the targets are newparams
class SIDREF(DaeObject):
    def __init__(self, data, value, scoped_node_for_sids, xmlnode=None):
        self.data = data   # the Collada object
        self.value = value
        self.scoped_node_for_sids = scoped_node_for_sids
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.SIDREF()
            self.save(0)
        
    def __deepcopy__(self, memodict):
        obj = SIDREF(self.data, copy.deepcopy(self.value), copy.deepcopy(self.scoped_node_for_sids), copy.deepcopy(self.xmlnode))
        obj.__class__ = self.__class__
        return obj
    
    @staticmethod
    def load( collada, localscope, scoped_node_for_sids, node ):
        value = node.text
        return SIDREF(collada, value, scoped_node_for_sids, node)
    
    def save(self, recurse=True):
        self.xmlnode.text = self.value
    
    def getchildren(self):
        return []
    
    def resolve(self):
        id_and_sids = self.value.split('/')
        node = self.data.ids_map.get(id_and_sids[0],None)

        prev_node = node
        for sid in id_and_sids[1:]:
            (best_sid_node,best_chain_length) = (None,None)
            for sid_node in self.data.sids_map.get(sid,[]):
                sid_pn_xmlnode = sid_node.xmlnode
                chain_length = 0
                while sid_pn_xmlnode is not None and sid_pn_xmlnode != prev_node.xmlnode:
                    chain_length += 1
                    sid_pn_xmlnode = sid_pn_xmlnode.getparent()
                if sid_pn_xmlnode is not None and (not best_sid_node or chain_length < best_chain_length):
                    (best_sid_node,best_chain_length) = (sid_node,chain_length)

            if not best_sid_node:
                # FIXME: throw an error
                return None


            # FIXME: better not to use xmlnode
            if best_sid_node.xmlnode.attrib.has_key('url'):
                new_id = best_sid_node.xmlnode.attrib['url'].lstrip('#')
                new_node = self.data.ids_map.get(new_id,None)
                if new_node is None:
                    return None
                else:
                    prev_node = new_node
            else:
                prev_node = best_sid_node

        return prev_node
