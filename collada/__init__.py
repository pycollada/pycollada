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

"""Main module for collada (pycollada) package.

You will find here class `Collada` which is the one to use to access
collada file, and some exceptions that are raised in case the input
file is not what is expected.

"""

from lxml import etree as ElementTree
from lxml.builder import ElementMaker
import zipfile
from StringIO import StringIO
import types
import traceback
from datetime import datetime
import posixpath
import os.path


E = ElementMaker(namespace='http://www.collada.org/2005/11/COLLADASchema',
                 nsmap={None: 'http://www.collada.org/2005/11/COLLADASchema'})
def tag( text ):
    return str(ElementTree.QName( 'http://www.collada.org/2005/11/COLLADASchema', text ))

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

    def __str__(self): return type(self).__name__ + ': ' + self.msg
    def __repr__(self): return type(self).__name__ + '("' + self.msg + '")'

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

import geometry
import scene
import material
import camera
import light
import controller
from util import IndexedList

class Collada(object):
    """This is the main class used to create and load collada documents"""

    def __init__(self, filename, ignore = [], aux_file_loader = None):
        """Load collada data from filename or file like object.
        
        :param filename:
          String containing path to filename to open or file-like object.
          Uncompressed .dae files are supported, as well as zip file archives.
        :param list ignore:
          A list of :class:`collada.DaeError` types that should be ignored
          when loading the collada document. Instances of these types will
          be added to :attr:`errors` after loading but won't be raised.
        :param function aux_file_loader:
          Referenced files (e.g. texture images) are loaded from disk when
          reading from the local filesystem and from the zip archive when
          loading from a zip file. If you these files are coming from another
          source (e.g. database) and you're loading with StringIO, set this to
          a function that given a filename, returns the binary data in the file.
        """
        
        self.errors = []
        """List of :class:`collada.DaeError` objects representing errors encounterd while loading collada file"""
        self.assetInfo = {}
        """A dictionary structure that stores asset information coming from <asset> tag"""
        self.geometries = IndexedList([], ('id',))
        """A list of :class:`collada.geometry.Geometry` objects. Can also be indexed by id"""
        self.controllers = IndexedList([], ('id',))
        """A list of :class:`collada.controller.Controller` objects. Can also be indexed by id"""
        self.lights = IndexedList([], ('id',))
        """A list of :class:`collada.light.Light` objects. Can also be indexed by id"""
        self.cameras = IndexedList([], ('id',))
        """A list of :class:`collada.camera.Camera` objects. Can also be indexed by id"""
        self.images = IndexedList([], ('id',))
        """A list of :class:`collada.material.CImage` objects. Can also be indexed by id"""
        self.effects = IndexedList([], ('id',))
        """A list of :class:`collada.material.Effect` objects. Can also be indexed by id"""
        self.materials = IndexedList([], ('id',))
        """A list of :class:`collada.material.Effect` objects. Can also be indexed by id"""
        self.nodes = IndexedList([], ('id',))
        """A list of :class:`collada.scene.Node` objects. Can also be indexed by id"""
        self.scenes = IndexedList([], ('id',))
        """A list of :class:`collada.scene.Scene` objects. Can also be indexed by id"""
        
        self.maskedErrors = []
        self.ignoreErrors( *ignore )
        
        if type(filename) in [types.StringType, types.UnicodeType]:
            fdata = open(filename, 'rb')
            self.filename = filename
            self.getFileData = self._getFileFromDisk
        else:
            fdata = filename # assume it is a file like object
            self.filename = None
            self.getFileData = self._nullGetFile
        strdata = fdata.read()
        
        try:
            self.zfile = zipfile.ZipFile(StringIO(strdata), 'r')
        except:
            self.zfile = None
        
        if self.zfile:
            self.filename = ''
            daefiles = []
            for name in self.zfile.namelist():
                if name.upper().endswith('.DAE'):
                    daefiles.append(name)
            for name in daefiles:
                if not self.filename:
                    self.filename = name
                elif "MACOSX" in self.filename:
                    self.filename = name
            if not self.filename: raise DaeIncompleteError('No DAE found inside zip compressed file')
            data = self.zfile.read(self.filename)
            self.getFileData = self._getFileFromZip
        else:
            data = strdata
        
        if aux_file_loader is not None:
            self.getFileData = aux_file_loader
        
        self.root = ElementTree.ElementTree(element=None, file=StringIO(data),
                                            parser=ElementTree.XMLParser(remove_comments=True))
        
        self._loadAssetInfo()
        self._loadImages()
        self._loadEffects()
        self._loadMaterials()
        self._loadGeometry()
        self._loadControllers()
        self._loadLights()
        self._loadCameras()
        self._loadNodes()
        self._loadScenes()
        self._loadDefaultScene()

    def handleError(self, error):
        self.errors.append(error)
        if not type(error) in self.maskedErrors:
            raise

    def ignoreErrors(self, *args):
        """Add exceptions to the mask for ignoring or clear the mask if None given.

        You call c.ignoreErrors(e1, e2, ... ) if you want the loader to ignore those
        exceptions and continue loading whatever it can. If you want to empty the
        mask so all exceptions abort the load just call c.ignoreErrors(None).

        """
        if args == [ None ]:
            self.maskedErrors = []
        else:
            for e in args: self.maskedErrors.append(e)
    
    def _getFileFromZip(self, fname):
        """Return the binary data of an auxiliary file from a zip archive as a string."""
        if not self.zfile:
            raise DaeBrokenRefError('Trying to load an auxiliar file %s but we are not reading from a zip'%fname)
        basepath = posixpath.dirname(self.filename)
        aux_path = posixpath.normpath(posixpath.join(basepath, fname))
        if aux_path not in self.zfile.namelist():
            raise DaeBrokenRefError('Auxiliar file %s not found in archive'%fname)
        return self.zfile.read( aux_path )

    def _getFileFromDisk(self, fname):
        """Return the binary data of an auxiliary file from the local disk relative to the file path loaded."""
        if self.zfile:
            raise DaeBrokenRefError('Trying to load an auxiliar file %s from disk but we are reading from a zip file'%fname)
        basepath = os.path.dirname(self.filename)
        aux_path = os.path.normpath(os.path.join(basepath, fname))
        if not os.path.exists(aux_path):
            raise DaeBrokenRefError('Auxiliar file %s not found on disk'%fname)
        fdata = open(aux_path, 'rb')
        return fdata.read()
    
    def _nullGetFile(self, fname):
        raise DaeBrokenRefError('Trying to load auxiliary file but collada was not loaded from disk, zip, or with custom handler')

    def _loadAssetInfo(self):
        """Load information in <asset> tag"""
        assetnode = self.root.find( tag('asset') )
        if assetnode != None:
            for subnode in list(assetnode):
                if subnode.tag == tag('up_axis'):
                    self.assetInfo['up_axis'] = subnode.text
                    if subnode.text is None:
                       self.assetInfo['up_axis'] = 'Y_UP'
                    if not( self.assetInfo['up_axis'] == 'X_UP' or self.assetInfo['up_axis'] == 'Y_UP' or self.assetInfo['up_axis'] == 'Z_UP' ):
                        raise DaeMalformedError('up_axis was unknown value of %s' % subnode.text)
                elif subnode.tag == tag('contributor'):
                    contributor_info = {}
                    for subsubnode in list(subnode):
                        if subsubnode.tag == tag('author'):
                            contributor_info['author'] = subsubnode.text
                        elif subsubnode.tag == tag('authoring_tool'):
                            contributor_info['authoring_tool'] = subsubnode.text
                        elif subsubnode.tag == tag('comments'):
                            contributor_info['comments'] = subsubnode.text
                        elif subsubnode.tag == tag('copyright'):
                            contributor_info['copyright'] = subsubnode.text
                        elif subsubnode.tag == tag('source_data'):
                            contributor_info['source_data'] = subsubnode.text
                    self.assetInfo['contributor'] = contributor_info
                elif subnode.tag == tag('unit'):
                    name = subnode.get('name')
                    meter = subnode.get('meter')
                    try:
                        if not meter is None: meter = float(meter)
                    except ValueError, ex: raise DaeMalformedError('Corrupted meter value in unit tag')
                    self.assetInfo['unit'] = {'name':name, 'meter':meter}
                elif subnode.tag == tag('created'):
                    try: self.assetInfo['created'] = datetime.strptime(subnode.text, "%Y-%m-%dT%H:%M:%SZ" )
                    except: pass
                elif subnode.tag == tag('modified'):
                    try: self.assetInfo['modified'] = datetime.strptime(subnode.text, "%Y-%m-%dT%H:%M:%SZ" )
                    except: pass
                elif subnode.tag == tag('revision'):
                    self.assetInfo['revision'] = subnode.text
        if not 'up_axis' in self.assetInfo:
            self.assetInfo['up_axis'] = 'Y_UP'
                    
    def _loadGeometry(self):
        """Load geometry library."""
        libnode = self.root.find( tag('library_geometries') )
        if libnode != None:
            for geomnode in libnode.findall(tag('geometry')):
                if geomnode.find(tag('mesh')) is None: continue
                try: G = geometry.Geometry.load( self, {}, geomnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.geometries.append( G )
    
    def _loadControllers(self):
        """Load controller library."""
        libnode = self.root.find( tag('library_controllers') )
        if libnode != None:
            for controlnode in libnode.findall(tag('controller')):
                if controlnode.find(tag('skin')) is None and controlnode.find(tag('morph')) is None:
                    continue
                try: C = controller.Controller.load( self, {}, controlnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.controllers.append( C )
    
    def _loadLights(self):
        """Load light library."""
        libnode = self.root.find( tag('library_lights') )
        if libnode != None:
            for lightnode in libnode.findall(tag('light')):
                try: lig = light.Light.load( self, {}, lightnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.lights.append( lig )

    def _loadCameras(self):
        """Load camera library."""
        libnode = self.root.find( tag('library_cameras') )
        if libnode != None:
            for cameranode in libnode.findall(tag('camera')):
                try: cam = camera.Camera.load( self, {}, cameranode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.cameras.append( cam )

    def _loadImages(self):
        """Load image library."""
        libnode = self.root.find( tag('library_images') )
        if libnode != None:
            for imgnode in libnode.findall(tag('image')):
                try: img = material.CImage.load( self, {}, imgnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.images.append( img )

    def _loadEffects(self):
        """Load effect library."""
        libnode = self.root.find( tag('library_effects') )
        if libnode != None:
            for effectnode in libnode.findall(tag('effect')):
                try: effect = material.Effect.load( self, {}, effectnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.effects.append( effect )

    def _loadMaterials(self):
        """Load material library."""
        libnode = self.root.find( tag('library_materials'))
        if libnode != None:
            for materialnode in libnode.findall(tag('material')):
                try: mat = material.Material.load( self, {}, materialnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.materials.append( mat )

    def _loadNodes(self):
        libnode = self.root.find( tag('library_nodes') )
        if libnode != None:
            for node in libnode.findall(tag('node')):
                try: N = scene.loadNode(self, node)
                except DaeError, ex: self.handleError(ex)
                else:
                    if N is not None:
                        self.nodes.append( N )

    def _loadScenes(self):
        """Load scene library."""
        libnode = self.root.find( tag('library_visual_scenes') )
        if libnode != None:
            for scenenode in libnode.findall(tag('visual_scene')):
                try: S = scene.Scene.load( self, scenenode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.scenes.append( S )

    def _loadDefaultScene(self):
        """Loads the default scene from <scene> tag in the root node."""
        node = self.root.find('%s/%s'%( tag('scene'), tag('instance_visual_scene') ) )
        self.scene = None
        try:
            if node != None:
                sceneid = node.get('url')
                if not sceneid.startswith('#'):
                    raise DaeMalformedError('Malformed default scene reference to %s: '%sceneid)
                self.scene = self.scenes.get(sceneid[1:])
                if not self.scene:
                    raise DaeBrokenRefError('Default scene %s not found'%sceneid)
        except DaeError, ex: self.handleError(ex)

    def save(self):
        """Save back all the data to the xml tree."""
        for img in self.images:
            img.save()
        for effect in self.effects:
            effect.save()
        for geom in self.geometries:
            geom.save()
        for scene in self.scenes:
            scene.save()


