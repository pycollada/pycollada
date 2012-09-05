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
"""Contains <technique> definitions"""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree

class Technique(DaeObject):
    def __init__(self, collada, profile, xmlns=None, xmlnode=None):
        self.collada = collada
        self.profile = profile
        self.xmlns = xmlns
        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.technique()
            self.save()

    def save(self):
        """Saves the info back to :attr:`xmlnode`"""
        self.xmlnode.set('profile',profile)
        if self.xmlns is not None:
            self.xmlnode.set('xmlns',self.xmlns)
        else:
            self.xmlnode.attrib.pop('xmlns',None)
