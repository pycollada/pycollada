from .common import DaeObject

class SIDREF(DaeObject):
    def __init__(self, value, scoped_node_for_sids, xmlnode):
        self.value = value
        self.scoped_node_for_sids = scoped_node_for_sids
        self.xmlnode = xmlnode

    @staticmethod
    def load( collada, localscope, scoped_node_for_sids, node ):
        value = node.text
        return SIDREF(value, scoped_node_for_sids, node)
