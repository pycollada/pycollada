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

"""Main module for collada (PyCollada) package.

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


E = ElementMaker(namespace='http://www.collada.org/2005/11/COLLADASchema',
                 nsmap={None: 'http://www.collada.org/2005/11/COLLADASchema'})
def tag( text ):
    return str(ElementTree.QName( 'http://www.collada.org/2005/11/COLLADASchema', text ))

class DaeObject(object):
    """This class is the interface to all DAE objects loaded from a file.

    Every <tag> in a COLLADA that we recognize and load has mirror
    class deriving from this one. It can be load() and save() according
    to methods defined here. All instances will have at least an attribute
    called "xmlnode" with the ElementTree representation of the data. Even if
    it was created on the fly.

    """

    xmlnode = None
    """ElementTree representation of the data."""

    @staticmethod
    def load(collada, localscope, node):
        """Load and return a class instance from an XML node.

        Inspect the data inside node, which must match
        this class tag and create an instance out of it.

        :Parameters:
          collada
            The collada file object where this object lives
          localscope
            If there is a local scope where we should look for local ids 
            (sid) this is the dictionary. Otherwise empty dict ({})
          node
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

class Collada(object):
    """Class used to access collada (dae,zae,kmz) files.

    It is able to load scenes from a file and access the supported
    data in an easy way. Supports plain xml DAE files or zip compressed
    structures like zae or kmz.

    """

    def __init__(self, filename, ignore = []):
        try:
            """Load collada data from filename or file like object."""
            if type(filename) in [types.StringType, types.UnicodeType]:
                fdata = open(filename, 'rb')
            else:
                fdata = filename # assume it is a file like object
            strdata = fdata.read()
            
            try:
                self.zfile = zipfile.ZipFile(StringIO(strdata), 'r')
            except:
                self.zfile = None
            
            if self.zfile:
                self.filename = ''
                for name in self.zfile.namelist():
                    if name.upper().endswith('.DAE'):
                        self.filename = name
                        break
                if not self.filename: raise DaeIncompleteError('No DAE found inside zip compressed file')
                data = self.zfile.read(self.filename)
            else:
                data = strdata
            
            self.errors = []
            self.maskedErrors = []
            self.ignoreErrors( *ignore )
            self.root = ElementTree.ElementTree(element=None, file=StringIO(data))
            self.validate()
            self.loadAssetInfo()
            self.loadImages()
            self.loadEffects()
            self.loadMaterials()
            self.loadGeometry()
            self.loadControllers()
            self.loadLights()
            self.loadNodes()
            self.loadCameras()
            self.loadScenes()
            self.loadDefaultScene()
        except:
            raise

    def validate(self):
        """TODO: Validate the xml tree."""
        pass

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

    def getFileData(self, fname):
        """Return the binary data from an auxiliary file as a string."""
        if not self.zfile:
            raise DaeBrokenRefError('Trying to load an auxiliar file %s but we are not reading from a zip'%fname)
        basepath = self.filename.split('/')[:-1]
        if fname.startswith('/'): fname = fname[1:]
        else:
            while fname.startswith('../') and basepath:
                fname = fname[3:]
                basepath = basepath[:-1]
            if basepath: fname = '/'.join(basepath) + '/' + fname
        if fname not in self.zfile.namelist():
            raise DaeBrokenRefError('Auxiliar file %s not found in archive'%fname)
        return self.zfile.read( fname )

    def loadAssetInfo(self):
        """Load information in <asset> tag"""
        assetnode = self.root.find( tag('asset') )
        self.assetInfo = {}
        if assetnode != None:
            for subnode in list(assetnode):
                if subnode.tag == tag('up_axis'):
                    self.assetInfo['up_axis'] = subnode.text
                    if not( subnode.text == 'X_UP' or subnode.text == 'Y_UP' or subnode.text == 'Z_UP' ):
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
                    
    def loadGeometry(self):
        """Load geometry library."""
        self.geometries = []
        self.geometryById = {}
        libnode = self.root.find( tag('library_geometries') )
        if libnode != None:
            for geomnode in libnode.findall(tag('geometry')):
                if geomnode.find(tag('mesh')) is None: continue
                try: G = geometry.Geometry.load( self, {}, geomnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.geometries.append( G )
                    self.geometryById[ G.id ] = G
    
    def loadControllers(self):
        """Load controller library."""
        self.controllers = []
        self.controllerById = {}
        libnode = self.root.find( tag('library_controllers') )
        if libnode != None:
            for controlnode in libnode.findall(tag('controller')):
                if controlnode.find(tag('skin')) is None and controlnode.find(tag('morph')) is None:
                    continue
                try: C = controller.Controller.load( self, {}, controlnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.controllers.append( C )
                    self.controllerById[ C.id ] = C
    
    def loadLights(self):
        """Load light library."""
        self.lights = []
        self.lightById = {}
        libnode = self.root.find( tag('library_lights') )
        if libnode != None:
            for lightnode in libnode.findall(tag('light')):
                try: lig = light.Light.load( self, {}, lightnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.lights.append( lig )
                    self.lightById[ lig.id ] = lig

    def loadCameras(self):
        """Load camera library."""
        self.cameras = []
        self.cameraById = {}
        libnode = self.root.find( tag('library_cameras') )
        if libnode != None:
            for cameranode in libnode.findall(tag('camera')):
                try: cam = camera.Camera.load( self, {}, cameranode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.cameras.append( cam )
                    self.cameraById[ cam.id ] = cam

    def loadImages(self):
        """Load image library."""
        self.images = []
        self.imageById = {}
        libnode = self.root.find( tag('library_images') )
        if libnode != None:
            for imgnode in libnode.findall(tag('image')):
                try: img = material.CImage.load( self, {}, imgnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.images.append( img )
                    self.imageById[ img.id ] = img

    def loadEffects(self):
        """Load effect library."""
        self.effects = []
        self.effectById = {}
        libnode = self.root.find( tag('library_effects') )
        if libnode != None:
            for effectnode in libnode.findall(tag('effect')):
                try: effect = material.Effect.load( self, {}, effectnode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.effects.append( effect )
                    self.effectById[ effect.id ] = effect

    def loadMaterials(self):
        """Load material library.
        
        Materials are only treated as aliases for effects at the time.
        But this might change in the future.

        """
        self.materials = []
        self.materialById = {}
        libnode = self.root.find( tag('library_materials'))
        if libnode != None:
            for materialnode in libnode.findall(tag('material')):
                inseffnode = materialnode.find( tag('instance_effect'))
                if inseffnode is None: continue
                effectid = inseffnode.get('url')
                if not effectid.startswith('#'): 
                    self.handleError(DaeMalformedError('Corrupted effect reference in material'))
                else:
                    matid = materialnode.get('id')
                    effect = self.effectById.get(effectid[1:])
                    if not effect: 
                        self.handleError(DaeBrokenRefError('Effect not found: '+effectid))
                    else:
                        self.materials.append( effect )
                        self.materialById[matid] = effect

    def loadNodes(self):
        self.nodes = []
        self.nodeById = {}
        libnode = self.root.find( tag('library_nodes') )
        if libnode != None:
            for node in libnode.findall(tag('node')):
                try: N = scene.loadNode(self, node)
                except DaeError, ex: self.handleError(ex)
                else:
                    self.nodes.append( N )
                    self.nodeById[N.id] = N

    def loadScenes(self):
        """Load scene library."""
        self.scenes = []
        self.sceneById = {}
        libnode = self.root.find( tag('library_visual_scenes') )
        if libnode != None:
            for scenenode in libnode.findall(tag('visual_scene')):
                try: S = scene.Scene.load( self, scenenode )
                except DaeError, ex: self.handleError(ex)
                else:
                    self.scenes.append( S )
                    self.sceneById[S.id] = S

    def loadDefaultScene(self):
        """Loads the default scene from <scene> tag in the root node."""
        node = self.root.find('%s/%s'%( tag('scene'), tag('instance_visual_scene') ) )
        self.scene = None
        if node != None:
            sceneid = node.get('url')
            if not sceneid.startswith('#'):
                self.handleError( DaeMalformedError('Malformed default scene reference: '+sceneid) )
            self.scene = self.sceneById.get(sceneid[1:])
            if not self.scene:
                self.handleError( DaeBrokenRefError('Default scene %s not found'%sceneid) )

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


