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

import numpy
from .xmlutil import etree, ElementMaker, get_collada_ns, E

def tag(text):
    return str(etree.QName(get_collada_ns(), text))

_number_dtype = numpy.float32
def get_number_dtype():
    """Returns the dtype for all numbers stored in numpy arrays.
    Default is numpy.float32.
    """
    return _number_dtype

def _set_number_dtype(dtype=None):
    global _number_dtype
    if dtype is None:
        _number_dtype = numpy.float32
    else:
        _number_dtype = dtype

# The Python repr function has a smart dtoa implementation so it will convert,
# e.g., 0.1 to 0.1 instead of 0.1000000001
# Can't use this for 32-bit numbers because float(np.float32(v)) adds extra
# unused precision, so repr spits out garbage.
def float_format_func():
    if _number_dtype == numpy.float64:
        return lambda x: repr(_number_dtype(x))
    
    return lambda x: '%.9g' % x

def int_format_func():
    return lambda x: '%d' % x

def save_attribute(xmlnode, attribute, value):
    """saves an attribute to xmlnode
   :param value: if value is None, will remove the attribute if one exists
    """
    if value is not None:
        xmlnode.set(attribute, value)
    else:
        xmlnode.attrib.pop(attribute,None)

def save_child_object(xmlnode,tag, childobject, recurse=True):
    """Saves the DaeObject as a child of xmlnode with tag. 
    If xmlnode already contains such a child, removes it and adds a new one.

    :param childobject: derived from DaeObject. If childobject is None, will remove any children with the same tag from xmlnode
    :param recurse: if true, will call childobject.save, otherwise will not
    """
    for previouschild in xmlnode.findall(tag):
        xmlnode.remove(previouschild)
    if childobject is not None:
        if recurse:
            childobject.save(recurse)
        xmlnode.append(childobject.xmlnode)
    
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

    def save(self,recurse=True):
        """Put all the data to the internal xml node (xmlnode) so it can be serialized.
        :param recurse: if True, will call save on the child nodes, otherwise will only save info pertaining to this node
        """

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

