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

"""Contains objects representing animations."""

from collada import source
from collada.common import DaeObject, tag
from collada.common import DaeIncompleteError, DaeBrokenRefError, \
        DaeMalformedError, DaeUnsupportedError, DaeError

class INTERPOLATION:
    """An enum of the interpolation methods supported by COLLADA"""
    LINEAR = 'LINEAR'
    BEZIER = 'BEZIER'
    CARDINAL = 'CARDINAL'
    HERMITE = 'HERMITE'
    BSPLINE = 'BSPLINE'
    STEP = 'STEP'

class Sampler(DaeObject):
    """Class for holding animation sampling coming from <sampler> tags."""
    
    def __init__(self, id, inputs):
        self.id = id
        self.inputs = inputs
    
    @staticmethod
    def load( collada, localscope, node ):
        id = node.get('id') or ''
        
        inputs = []
        for input_node in node.findall(tag('input')):
            semantic = input_node.get('semantic')
            source = input_node.get('source')
            if not semantic or not source:
                raise DaeIncompleteError("Input node of animation sampler '%s' missing semantic or source" % id)
            if source[1:] not in localscope:
                raise DaeBrokenRefError("Input of animation sampler '%s' refering to source '%s' not found" % (id, source))
            inputs.append((semantic, source))
        
        return Sampler(id, inputs)
    
    def __str__(self): return '<Sampler id=%s>' % (self.id,)
    def __repr__(self): return str(self)

class Channel(DaeObject):
    """Class for holding animation channel coming from <channel> tags."""
    
    def __init__(self, source, target):
        self.source = source
        self.target = target
    
    @staticmethod
    def load( collada, localscope, node ):
        source = node.get('source')
        target = node.get('target')
        
        if not source or not target:
            raise DaeIncompleteError("Animation channel node missing source or target")
        if source[1:] not in localscope:
            raise DaeBrokenRefError("Input of animation channel '%s' not found" % (source))
        
        source = localscope[source[1:]]
        return Channel(source, target)
    
    def __str__(self): return '<Channel source=%s target=%s>' % (self.source, self.target)
    def __repr__(self): return str(self)

class Animation(DaeObject):
    """Class for holding animation data coming from <animation> tags."""

    def __init__(self, id, name, sourceById, samplers, channels, children, xmlnode=None):
        self.id = id
        self.name = name
        self.samplers = samplers
        self.channels = channels
        self.children = children
        self.sourceById = sourceById
        self.xmlnode = xmlnode
        if self.xmlnode is None:
            self.xmlnode = None

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get('id') or ''
        name = node.get('name') or ''

        sourcebyid = localscope
        sources = []
        sourcenodes = node.findall(tag('source'))
        for sourcenode in sourcenodes:
            ch = source.Source.load(collada, {}, sourcenode)
            sources.append(ch)
            sourcebyid[ch.id] = ch

        child_nodes = node.findall(tag('animation'))
        children = []
        for child in child_nodes:
            try:
                child = Animation.load(collada, sourcebyid, child)
                children.append(child)
            except DaeError as ex:
                collada.handleError(ex)

        samplers = []
        samplerById = {}
        for sampler_node in node.findall(tag('sampler')):
            try:
                sampler = Sampler.load(collada, sourcebyid, sampler_node)
                samplers.append(sampler)
                samplerById[sampler.id] = sampler
            except DaeError, ex: collada.handleError(ex)
        
        channels = []
        for channel_node in node.findall(tag('channel')):
            try:
                channel = Channel.load(collada, samplerById, channel_node)
                channels.append(channel)
            except DaeError, ex: collada.handleError(ex)
        
        anim = Animation(id, name, sourcebyid, samplers, channels, children, node)
        return anim

    def __str__(self): return '<Animation id=%s, sources=%d, children=%d>' % (self.id, len(self.sourceById), len(self.children))
    def __repr__(self): return str(self)
