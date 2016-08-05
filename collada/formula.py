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
"""Contains objects for representing a formula section."""

from .common import DaeObject, E, tag
from .common import DaeIncompleteError, DaeBrokenRefError, DaeMalformedError, DaeUnsupportedError
from .xmlutil import etree as ElementTree
import re

MATHML_URL = 'http://www.w3.org/1998/Math/MathML'

def mathtag(text):
    return str(ElementTree.QName(MATHML_URL, text))

def _replace(text, patterndict):
    rx = re.compile('|'.join(map(re.escape, patterndict)))

    def one_xlat(match):
        return patterndict[match.group(0)]

    return rx.sub(one_xlat, text)

class Target(DaeObject):
    def __init__(self, target, xmlnode=None):
        self.target = target

        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.target()
            self.save()

    @staticmethod
    def load(collada, localscope, node):
        # target is in subnode param text, assume there is only one target
        target = node.find(tag('target')).getchildren()[0].text
        node = Target(target, xmlnode=node.find(tag('target')))

        return node

    def save(self):
        self.xmlnode.clear()
        paramnode = ElementTree.Element(tag('param'))
        paramnode.text = self.target
        self.xmlnode.append(paramnode)


class Equation(DaeObject):
    def __init__(self, type, math=None, mathxmlstring=None, xmlnode=None):
        self.type = type

        self.math = ElementTree.Element(mathtag('math'))
        if math is not None:
            self.math = math

        self.mathxmlstring = _replace(ElementTree.tostring(self.math), {'\t':'', '\n':'', 'ns0:':'', ':ns0':''})
        if mathxmlstring is not None:
            self.mathxmlstring = mathxmlstring

        if xmlnode is not None:
            self.xmlnode = xmlnode
        else:
            self.xmlnode = E.equation()
            self.save()

    @staticmethod
    def load(collada, localscope, node):
        type = node.get('type')
        math = node.find(mathtag('math'))
        node = Equation(type, math=math, xmlnode=node)
        return node

    def save(self, recurse=True):
        """
        Currently not support equation editing
        :param recurse:
        :return:
        """
        self.xmlnode.clear()
        self.xmlnode.set('type', self.type)
        self.math = ElementTree.fromstring(self.mathxmlstring)
        self.xmlnode.append(self.math)

class Formula(DaeObject):
    def __init__(self, id, sid, target, equations=None, positioneqs=None, velocityeqs=None, accelerateeqs=None, xmlnode=None):

        self.id = id
        self.sid = sid
        self.target = target

        self.equations = []
        if equations is not None:
            self.equations = equations

        self.positioneqs = []
        if positioneqs is not None:
            self.positioneqs = positioneqs

        self.velocityeqs = []
        if velocityeqs is not None:
            self.velocityeqs = velocityeqs

        self.accelerateeqs = []
        if accelerateeqs is not None:
            self.accelerateeqs = accelerateeqs

        if xmlnode is not None:
            self.xmlnode = xmlnode

        else:
            self.xmlnode = E.formula()
            self.save(False)

    @staticmethod
    def load(collada, localscope, node):
        id = node.get("id")
        sid = node.get("sid")
        target = Target.load(collada, localscope, node)
        equation_nodes = node.find(tag('technique'))
        equations = [Equation.load(collada, localscope, enode) for enode in equation_nodes]
        node = Formula(id, sid, target,
                       equations=equations,
                       positioneqs=filter(lambda x: x.type == 'position', equations),
                       velocityeqs=filter(lambda x: x.type == 'first_partial', equations),
                       accelerateeqs=filter(lambda x: x.type == 'second_partial', equations), xmlnode=node)
        collada.addId(id, node)
        collada.addSid(sid, node)
        return node

    def getchildren(self):
        return self.equations

    def save(self, recurse=True):
        self.xmlnode.clear()

        if self.id is not None:
            self.xmlnode.set('id', self.id)
        else:
            self.xmlnode.attrib.pop('id', None)
        if self.sid is not None:
            self.xmlnode.set('sid', self.sid)
        else:
            self.xmlnode.attrib.pop('sid', None)

        if self.target is not None:
            self.xmlnode.append(self.target.xmlnode)

        techniquenode = ElementTree.Element(tag('technique'))
        techniquenode.set('profile', 'OpenRAVE')
        for equation in self.equations:
            if recurse:
                equation.save()
            techniquenode.append(equation.xmlnode)
        self.xmlnode.append(techniquenode)
