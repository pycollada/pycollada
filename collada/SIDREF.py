from .common import DaeObject

class SIDREF(DaeObject):
    def __init__(self, data, value, scoped_node_for_sids, xmlnode):
        self.data = data   # the Collada object
        self.value = value
        self.scoped_node_for_sids = scoped_node_for_sids
        self.xmlnode = xmlnode

    @staticmethod
    def load( collada, localscope, scoped_node_for_sids, node ):
        value = node.text
        return SIDREF(collada, value, scoped_node_for_sids, node)

    def resolve(self):
        id_and_sids = self.value.split('/')
        node = self.data.ids_map.get(id_and_sids[0],None)

        prev_node = node
        for sid in id_and_sids[1:]:
            print 'searching for',sid
            (best_sid_node,best_chain_length) = (None,None)
            for sid_node in self.data.sids_map.get(sid,[]):
                print 'found',sid_node
                sid_pn_xmlnode = sid_node.xmlnode
                chain_length = 0
                while sid_pn_xmlnode and sid_pn_xmlnode != prev_node.xmlnode:
                    chain_length += 1
                    sid_pn_xmlnode = sid_pn_xmlnode.getparent()
                if sid_pn_xmlnode and (not best_sid_node or chain_length < best_chain_length):
                    (best_sid_node,best_chain_length) = (sid_node,chain_length)

            if not best_sid_node:
                # FIXME: throw an error
                return None

            prev_node = best_sid_node

        return prev_node
