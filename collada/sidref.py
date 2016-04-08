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
        node = self.data.ids_map.get(id_and_sids[0], None)

        # use breath first search to look for the shallowest node with matching sid
        def _searchforsid(rootnode, sid):
            searchqueue = [rootnode]
            while len(searchqueue) > 0:
                node = searchqueue.pop(0)
                if node.xmlnode is not None and node.xmlnode.get('sid') == sid:
                    return node
                searchqueue.extend(node.getchildren())
            return None

        prev_node = node
        for sid in id_and_sids[1:]:
            best_sid_node = _searchforsid(prev_node, sid)
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
