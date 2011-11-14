from collada.xmlutil import etree, ElementMaker, COLLADA_NS

E = ElementMaker(namespace=COLLADA_NS, nsmap={None: COLLADA_NS})


def tag(text):
    return str(etree.QName(COLLADA_NS, text))


class DaeObject(object):
    """This class is the abstract interface to all collada objects.

    Every <tag> in a COLLADA that we recognize and load has mirror
    class deriving from this one. All instances will have at least
    a :meth:`load` method which creates the object from an xml node and
    an attribute called :attr:`xmlnode` with the ElementTree representation
    of the data. Even if it was created on the fly. If the object is
    not read-only, it will also have a :meth:`save` method which saves the
    object's information back to the :attr:`xmlnode` attribute.

    """

    xmlnode = None
    """ElementTree representation of the data."""

    @staticmethod
    def load(collada, localscope, node):
        """Load and return a class instance from an XML node.

        Inspect the data inside node, which must match
        this class tag and create an instance out of it.

        :param collada.Collada collada:
          The collada file object where this object lives
        :param dict localscope:
          If there is a local scope where we should look for local ids
          (sid) this is the dictionary. Otherwise empty dict ({})
        :param node:
          An Element from python's ElementTree API

        """
        raise Exception('Not implemented')

    def save(self):
        """Put all the data to the internal xml node (xmlnode) so it can be serialized."""

class DaeError(Exception):
    """General DAE exception."""
    def __init__(self, msg):
        super(DaeError,self).__init__()
        self.msg = msg

    def __str__(self):
        return type(self).__name__ + ': ' + self.msg

    def __repr__(self):
        return type(self).__name__ + '("' + self.msg + '")'

class DaeIncompleteError(DaeError):
    """Raised when needed data for an object isn't there."""
    pass

class DaeBrokenRefError(DaeError):
    """Raised when a referenced object is not found in the scope."""
    pass

class DaeMalformedError(DaeError):
    """Raised when data is found to be corrupted in some way."""
    pass

class DaeUnsupportedError(DaeError):
    """Raised when some unexpectedly unsupported feature is found."""
    pass

class DaeSaveValidationError(DaeError):
    """Raised when XML validation fails when saving."""
    pass

