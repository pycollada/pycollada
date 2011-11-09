import sys
import functools

HAVE_LXML = False

try:
    from lxml import etree
    HAVE_LXML = True
except ImportError:
    from xml.etree import ElementTree as etree

ET = etree

try:
    from functools import partial
except ImportError:
    # fake it for pre-2.5 releases
    def partial(func, tag):
        return lambda *args, **kwargs: func(tag, *args, **kwargs)

try:
    callable
except NameError:
    # Python 3
    def callable(f):
        return hasattr(f, '__call__')

try:
    basestring = __builtins__["basestring"]
except (NameError, KeyError):
    basestring = str

try:
    unicode = __builtins__["unicode"]
except (NameError, KeyError):
    unicode = str

if HAVE_LXML:
    from lxml.builder import E, ElementMaker
else:    
    class ElementMaker(object):
        def __init__(self, namespace=None, nsmap=None):
            if namespace is not None:
                self._namespace = '{' + namespace + '}'
            else:
                self._namespace = None
        
        def __call__(self, tag, *children, **attrib):
            if self._namespace is not None and tag[0] != '{':
                tag = self._namespace + tag
            
            elem = etree.Element(tag, attrib)
            for item in children:
                if isinstance(item, dict):
                    elem.attrib.update(item)
                elif isinstance(item, basestring):
                    if len(elem):
                        elem[-1].tail = (elem[-1].tail or "") + item
                    else:
                        elem.text = (elem.text or "") + item
                elif etree.iselement(item):
                    elem.append(item)
                else:
                    raise TypeError("bad argument: %r" % item)
            return elem
    
        def __getattr__(self, tag):
            return functools.partial(self, tag)

    E = ElementMaker()