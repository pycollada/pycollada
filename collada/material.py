####################################################################
#                                                                  #
# THIS FILE IS PART OF THE PyCollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE PyCollada SOURCE CODE IS (C) COPYRIGHT 2009                  #
# by Scopia Visual Interfaces Systems http://www.scopia.es/        #
#                                                                  #
####################################################################

"""Module for material, effect and image loading

This module contains all the functionality to load and manage:
- Images in the image library
- Surfaces and samplers2D in effects
- Effects (that are now used as materials)

"""

from xml.etree import ElementTree
import numpy
from collada import DaeObject, DaeIncompleteError, DaeBrokenRefError, \
                    DaeMalformedError, DaeUnsupportedError, tag
from StringIO import StringIO
try:
    import Image as pil
except:
    pil = None

class DaeMissingSampler2D(Exception):
    """Raised when a <texture> tag references a texture without a sampler."""
    pass

class CImage(DaeObject):
    """Class containing data coming from a <image> tag.

    Basicly is just the path to the file. but we give an extended
    functionality if PIL is available. You can in that case get the
    image object or numpy arrays in both int and float format. We
    named it CImage to avoid confusion with pil's Image class.

    """

    def __init__(self, id, path, collada = None, xmlnode = None):
        """Create an image object.
        
        :Parameters:
          id
            Id of the image node for later reference
          path
            Path in the [zae, kmz] file space
          collada
            The Collada class instance containing this for file access
          xmlnode
            If loaded from xml, the node this data comes from

        """
        self.id = id
        self.path = path
        self.collada = collada
        self._data = None
        self._pilimage = None
        self._uintarray = None
        self._floatarray = None
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('image') )
            initnode = ElementTree.Element( tag('init_from') )
            initnode.text = path
            self.xmlnode.append(initnode)
            self.xmlnode.set('id', id)
            self.xmlnode.set('name', id)

    def getData(self):
        if self._data is None:
            try: self._data = self.collada.getFileData( self.path )
            except DaeBrokenRefError, ex:
                self._data = ''
                self.collada.handleError(ex)
        return self._data
            
    def getImage(self):
        if pil is None or self._pilimage == 'failed': return None
        if self._pilimage: return self._pilimage
        else:
            data = self.getData()
            if not data: 
                self._pilimage = 'failed'
                return None
            #try: data = self.collada.getFileData( self.path )
            #except DaeBrokenRefError, ex:
            #    self._pilimage = 'failed'
            #    self.collada.handleError(ex)
            #    return None
            try: self._pilimage = pil.open( StringIO(data) )
            except IOError, ex: 
                self._pilimage = 'failed'
                print 'PIL failed to load image'
                return None
            return self._pilimage

    def getUintArray(self):
        if self._uintarray == 'failed': return None
        if self._uintarray != None: return self._uintarray
        img = self.getImage()
        if not img: 
            self._uintarray = 'failed'
            return None
        nchan = len(img.mode)
        self._uintarray = numpy.fromstring(img.tostring(), dtype=numpy.uint8)
        self._uintarray.shape = (img.size[1], img.size[0], nchan)
        return self._uintarray

    def getFloatArray(self):
        if self._floatarray == 'failed': return None
        if self._floatarray != None: return self._floatarray
        array = self.getUintArray()
        if array is None:
            self._floatarray = 'failed'
            return None
        self._floatarray = numpy.asarray( array, dtype=numpy.float32)
        self._floatarray *= 1.0/255.0
        return self._floatarray

    data = property( getData )
    """Image file data (any format) if the file is readable."""
    pilimage = property( getImage )
    """PIL Image object if PIL is available and the file is readable."""
    uintarray = property( getUintArray )
    """Numpy array (height, width, nchannels) in integer format."""
    floatarray = property( getFloatArray )
    """Numpy float array (height, width, nchannels) with the image data normalized to 1.0."""

    @staticmethod
    def load( collada, localspace, node ):
        id = node.get('id')
        initnode = node.find( tag('init_from') )
        if initnode is None: raise DaeIncompleteError('Image has no file path')
        path = initnode.text
        return CImage(id, path, collada, xmlnode = node)

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        initnode = self.xmlnode.find( tag('init_from') )
        initnode.text = self.path

class Surface(DaeObject):
    """Class containing data coming from a <surface> tag.

    Collada materials, for accessing image data create this
    tag that I guess makes sense in sombody's head. The only
    additional information is the format string.

    """

    def __init__(self, id, img, format, xmlnode=None):
        """Create a surface from an id in the local scope, image and format."""
        self.id = id
        """Id of the node in the local scope of the material."""
        self.image = img
        """CImage object from the image library."""
        self.format = format
        """Format string."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('newparam') )
            surfacenode = ElementTree.Element( tag('surface') )
            initnode = ElementTree.Element( tag('init_from') )
            initnode.text = self.image.id
            formatnode = ElementTree.Element( tag('format') )
            formatnode.text = 'A8R8G8B8'
            surfacenode.append( initnode )
            surfacenode.append( formatnode )
            self.xmlnode.append( surfacenode )
            self.xmlnode.set('sid', self.id)
            surfacenode.set('type', '2D')

    @staticmethod
    def load( collada, localscope, node ):
        surfacenode = node.find( tag('surface') )
        if surfacenode is None: raise DaeIncompleteError('No surface found in newparam')
        if surfacenode.get('type') != '2D': raise DaeMalformedError('Hard to imagine a non-2D surface, isn\'t it?')
        initnode = surfacenode.find( tag('init_from') )
        if initnode is None: raise DaeIncompleteError('No init image found in surface')
        formatnode = surfacenode.find( tag('format') )
        if formatnode is None: format = None #raise Exception('No format found in surface')
        else: format = formatnode.text
        imgid = initnode.text
        id = node.get('sid')
        img = collada.imageById.get(imgid)
        if img is None: raise DaeBrokenRefError('Missing image ' + imgid)
        return Surface(id, img, format, xmlnode=node)

    def save(self):
        surfacenode = self.xmlnode.find( tag('surface') )
        initnode = surfacenode.find( tag('init_from') )
        if self.format:
            formatnode = surfacenode.find( tag('format') )
            formatnode.text = self.format
        initnode.text = self.image.id
        self.xmlnode.set('sid', self.id)

class Sampler2D(DaeObject):
    """Class containing data coming from <sampler2D> tag in material.

    If <surface> tag wasn't enough, you also need this in the material
    in order to map an image. But as opposed to surface this has
    magnification and minification filter information that might be
    useful for some applications.

    """

    def __init__(self, id, surface, minfilter, maxfilter, xmlnode=None):
        """Create a sampler object.
        
        :Parameters:
          id
            Id of the node in the local scope of the material
          surface
            Surface instance that this object samples from
          minfilter
            Minification filter string id, see collada specs
          maxfilter
            Maximization filter string id, see collada specs
          maxfilter
            If loaded from XML, the node data comes from

        """
        self.id = id
        """Id in the local scope of the material."""
        self.surface = surface
        """Surface class instance this object samples from."""
        self.minfilter = minfilter
        """Minification filter string id, see collada specs."""
        self.maxfilter = maxfilter
        """Maximization filter string id, see collada specs."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('newparam') )
            samplernode = ElementTree.Element( tag('sampler2D') )
            sourcenode = ElementTree.Element( tag('source') )
            sourcenode.text = self.surface.id
            samplernode.append( sourcenode )
            if minfilter: 
                minnode = ElementTree.Element( tag('minfilter') )
                minnode.text = self.minfilter
                samplernode.append( minnode )
            if maxfilter: 
                maxnode = ElementTree.Element( tag('maxfilter') )
                maxnode.text = self.maxfilter
                samplernode.append( maxnode )
            self.xmlnode.append( samplernode )
            self.xmlnode.set('sid', self.id)

    @staticmethod
    def load( collada, localscope, node ):
        samplernode = node.find( tag('sampler2D') )
        if samplernode is None: raise DaeIncompleteError('No sampler found in newparam')
        sourcenode = samplernode.find( tag('source') )
        if sourcenode is None: raise DaeIncompleteError('No source found in sampler')
        minnode = samplernode.find( tag('minfilter') )
        if minnode is None: minfilter = None
        else: minfilter = minnode.text
        maxnode = samplernode.find( tag('maxfilter') )
        if maxnode is None: maxfilter = None
        else: maxfilter = maxnode.text

        surfaceid = sourcenode.text
        id = node.get('sid')
        surface = localscope.get(surfaceid)
        if surface is None or type(surface) != Surface: raise DaeBrokenRefError('Missing surface ' + surfaceid)
        return Sampler2D(id, surface, minfilter, maxfilter, xmlnode=node)

    def save(self):
        samplernode = self.xmlnode.find( tag('sampler2D') )
        sourcenode = samplernode.find( tag('source') )
        if self.minfilter:
            minnode = samplernode.find( tag('minfilter') )
            minnode.text = self.minfilter
        if self.maxfilter:
            maxnode = samplernode.find( tag('maxfilter') )
            maxnode.text = self.maxfilter
        sourcenode.text = self.surface.id
        self.xmlnode.set('sid', self.id)

class Map(DaeObject):
    """Class containing data coming from <texture> tag inside material.

    When a material defines its properties like "diffuse" it can give you
    a color or a texture. In the latter you'll find something like
    <texture texcoord="CHANNEL1" texture="primer_jpg-sampler"/>
    That in addition to the sampler to use, specifies the texcoord channel
    to use for the mapping. If a material defined a texture for one of its
    properties, you'll find an object of this class in the corresponding
    attribute.

    """

    def __init__(self, sampler, texcoord, xmlnode=None):
        """Create a Map instance to a sampler using a texcoord channel.

        :Parameters:
          sampler
            A Sampler object to map.
          texcoord
            Texture coord channel symbol to use.
          xmlnode
            If loaded from XML, the node data comes from.

        """
        self.sampler = sampler
        """Sampler object to map."""
        self.texcoord = texcoord
        """Texture coord channel symbol to use."""
        if xmlnode != None: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('texture') )
            self.xmlnode.set('texture', self.sampler.id)
            self.xmlnode.set('texcoord', self.texcoord)
    
    @staticmethod
    def load( collada, localscope, node ):
        samplerid = node.get('texture')
        texcoord = node.get('texcoord')
        sampler = localscope.get(samplerid)
        #Check for the sampler ID as the texture ID because some exporters suck
        if sampler is None:
            for s2d in localscope.itervalues():
                if type(s2d) is Sampler2D:
                    if s2d.surface.image.id == samplerid:
                        sampler = s2d
        if sampler is None or type(sampler) != Sampler2D:
            err = DaeMissingSampler2D('Missing sampler ' + samplerid + ' in node ' + node.tag)
            err.samplerid = samplerid
            raise err
        return Map(sampler, texcoord, xmlnode = node)

    def save(self):
        self.xmlnode.set('texture', self.sampler.id)
        self.xmlnode.set('texcoord', self.texcoord)

class Effect(DaeObject):
    """Class containing data coming from a <effect> tag.

    Since we don't have a Material class (so far, material seems
    to be used only as an alias for an effect) this is what actually
    represents a material.

    """
    supported = [ 'emission', 'ambient', 'diffuse', 'specular',
                  'shininess', 'reflective', 'reflectivity',
                  'transparent', 'transparency' ]
    """Supported material properties list."""
    shaders = [ 'phong', 'lambert', 'blinn', 'constant']
    """Supported shader list."""
    
    def __init__(self, id, params, shadingtype,
                       emission = (0.0, 0.0, 0.0),
                       ambient = (0.0, 0.0, 0.0),
                       diffuse = (0.0, 0.0, 0.0),
                       specular = (0.0, 0.0, 0.0),
                       shininess = 0.0,
                       reflective = (0.0, 0.0, 0.0),
                       reflectivity = 0.0,
                       transparent = (0.0, 0.0, 0.0),
                       transparency = 0.0,
                       xmlnode = None):
        """Create an effect instance out of properties.

        :Parameters
          id
            Id in the effect library.
          params
            A dictionary with the 'sampler' and 'surface2D'
            objects indexed by their sid's in case we are
            using textures.
          shadingtype
            The tag of the node this properties are coming
            from. At the moment we are only parsing shader types
            listed in Effect.shaders. This could be refactored in
            the future if a strong support for materials is needed.
          emission : 3-float tuple (RGB)
            property
          ambient : 3-float tuple (RGB)
            property
          diffuse : 3-float tuple (RGB)
            property
          specular : 3-float tuple (RGB)
            property
          shininess : float
            property
          reflective : 3-float tuple (RGB)
            property
          reflectivity : float
            property
          transparent : 3-float tuple (RGB)
            property
          transparency : float
            property
          xmlnode:
            If loaded from XML, the node data comes from.

        """
        self.id = id
        self.params = params
        """Local ditionary of sampler2D and surface objects."""
        self.shadingtype = shadingtype
        """String with the type of the shading."""
        self.emission = emission
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflective = reflective
        self.reflectivity = reflectivity
        self.transparent = transparent
        self.transparency = transparency
        if xmlnode: self.xmlnode = xmlnode
        else:
            self.xmlnode = ElementTree.Element( tag('effect') )
            self.xmlnode.set('id', self.id)
            self.xmlnode.set('name', self.id)
            profilenode = ElementTree.Element( tag('profile_COMMON') )
            self.xmlnode.append(profilenode)
            for param in self.params: profilenode.append( param.xmlnode )
            tecnode = ElementTree.Element( tag('technique') )
            profilenode.append(tecnode)
            tecnode.set('sid', 'common')
            shadnode = ElementTree.Element( tag(self.shadingtype) )
            tecnode.append(shadnode)
            for prop in self.supported:
                value = getattr(self, prop)
                if value is None: continue
                propnode = ElementTree.Element( tag(prop) )
                shadnode.append( propnode )
                if type(value) is Map: propnode.append( value.xmlnode )
                elif type(value) is float:
                    floatnode = ElementTree.ElementTree( tag('float') )
                    floatnode.text = str(value)
                    propnode.append(floatnode)
                else:
                    colornode = ElementTree.ElementTree( tag('color') )
                    colornode.text = ' '.join( [ str(v) for v in value] )
                    propnode.append(colornode)

    @staticmethod
    def load(collada, localscope, node):
        localscope = {} # we have our own scope, shadow it
        params = []
        id = node.get('id')
        profilenode = node.find( tag('profile_COMMON') )
        if profilenode is None:
            raise DaeUnsupportedError('Found effect with profile other than profile_COMMON')
        for paramnode in profilenode.findall( tag('newparam') ):
            if paramnode.find( tag('surface') ) != None:
                param = Surface.load(collada, localscope, paramnode)
            elif paramnode.find( tag('sampler2D') ) != None:
                param = Sampler2D.load(collada, localscope, paramnode)
            params.append(param)
            localscope[param.id] = param
        tecnode = profilenode.find( tag('technique') )
        shadnode = None
        for shad in Effect.shaders:
            shadnode = tecnode.find(tag(shad))
            shadingtype = shad
            if not shadnode is None:
                break
        if shadnode is None: raise DaeIncompleteError('No material properties found in effect')
        props = {}
        for key in Effect.supported:
            pnode = shadnode.find( tag(key) )
            if pnode is None: props[key] = None
            else:
                try: props[key] = Effect.loadShadingParam(collada, localscope, pnode)
                except DaeMissingSampler2D, ex:
                    if ex.samplerid in collada.imageById:
                        #Whoever exported this collada file didn't include the proper references so we will create them
                        surf = Surface(ex.samplerid + '-surface', collada.imageById[ex.samplerid], 'A8R8G8B8')
                        sampler = Sampler2D(ex.samplerid, surf, None, None);
                        params.append(surf)
                        params.append(sampler)
                        localscope[surf.id] = surf
                        localscope[sampler.id] = sampler
                        try: props[key] = Effect.loadShadingParam(collada, localscope, pnode)
                        except DaeUnsupportedError, ex:
                            props[key] = None
                            collada.handleError(ex)
                except DaeUnsupportedError, ex:
                    props[key] = None
                    collada.handleError(ex) # Give the chance to ignore error and load the rest
        props['xmlnode'] = node
        return Effect(id, params, shadingtype, **props)

    @staticmethod
    def loadShadingParam( collada, localscope, node ):
        """Load from the node a definition for a material property."""
        children = node.getchildren()
        if not children: raise DaeIncompleteError('Incorrect effect shading parameter '+key)
        vnode = children[0]
        if vnode.tag == tag('color'):
            try: value = tuple([ float(v) for v in vnode.text.split() ])[:3]
            except ValueError, ex: raise DaeMalformedError('Corrupted color definition in effect '+id)
            except IndexError, ex: raise DaeMalformedError('Corrupted color definition in effect '+id)
        elif vnode.tag == tag('float'):
            try: value = float(vnode.text)
            except ValueError, ex: raise DaeMalformedError('Corrupted float definition in effect '+id)
        elif vnode.tag == tag('texture'):
            value = Map.load(collada, localscope, vnode)
        else: raise DaeUnsupportedError('Unknown shading param definition ' + vnode.tag)
        return value

    def save(self):
        self.xmlnode.set('id', self.id)
        self.xmlnode.set('name', self.id)
        profilenode = self.xmlnode.find( tag('profile_COMMON') )
        for param in self.params: param.save()
        tecnode = profilenode.find( tag('technique') )
        tecnode.set('sid', 'common')
        for shad in self.shaders:
            shadnode = tecnode.find(tag(shad))
            if not shadnode is None:
                break
        for prop in self.supported:
            value = getattr(self, prop)
            if value is None: continue
            propnode = shadnode.find( tag(prop) )
            if type(value) is Map: value.save()
            elif type(value) is float:
                floatnode = propnode.find( tag('float') )
                floatnode.text = str(value)
            else:
                colornode = propnode.find( tag('color') )
                colornode.text = ' '.join( [ str(v) for v in value] )

