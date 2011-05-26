#!/usr/bin/env python

import collada
import numpy
import sys

def inspectController(controller):
    """Display contents of a controller object found in the scene."""
    print '    Controller (id=%s) (type=%s)' % (controller.skin.id, type(controller).__name__)
    print '       Vertex weights:%d, joints:%d' % (len(controller), len(controller.joint_matrices))
    for controlled_prim in controller.primitives():
        print '       Primitive', type(controlled_prim.primitive).__name__

def inspectGeometry(obj):
    """Display contents of a geometry object found in the scene."""
    materials = set()
    for prim in obj.primitives():
        materials.add( prim.material )

    print '    Geometry (id=%s): %d primitives'%(obj.original.id, len(obj))
    for prim in obj.primitives():
        print '        Primitive (type=%s): len=%d vertices=%d' % (type(prim).__name__, len(prim), len(prim.vertex))
    for mat in materials:
        if mat: inspectMaterial( mat )

def inspectMaterial(mat):
    """Display material contents."""
    print '        Material %s: shading %s'%(mat.effect.id, mat.effect.shadingtype)
    for prop in mat.effect.supported:
        value = getattr(mat.effect, prop)
        # it can be a float, a color (tuple) or a Map ( a texture )
        if isinstance(value, collada.material.Map):
            colladaimage = value.sampler.surface.image
            # Accessing this attribute forces the loading of the image
            # using PIL if available. Unless it is already loaded.
            img = colladaimage.pilimage
            if img: # can read and PIL available
                print '            %s = Texture %s:'%(prop, colladaimage.id),\
                      img.format, img.mode, img.size
            else:
                print '            %s = Texture %s: (not available)'%(
                                   prop, colladaimage.id)
        else:
            print '            %s ='%(prop), value

def inspectCollada(col):
    # Display the file contents
    print 'File Contents:'
    print '  Asset Info:'
    if 'contributor' in col.assetInfo:
        contribDict = col.assetInfo['contributor']
        if 'author' in contribDict:
            print '    Author: ', contribDict['author']
        if 'authoring_tool' in contribDict:
            print '    Authoring Tool: ', contribDict['authoring_tool']
    print '  Geometry:'
    if col.scene is not None:
        for geom in col.scene.objects('geometry'):
            inspectGeometry( geom )
    print '  Controllers:'
    if col.scene is not None:
        for controller in col.scene.objects('controller'):
            inspectController( controller )
    print '  Cameras:'
    if col.scene is not None:
        for cam in col.scene.objects('camera'):
            print '    Camera %s: '%cam.original.id
    print '  Lights:'
    if col.scene is not None:
        for light in col.scene.objects('light'):
            print '    Light %s: color =' % light.original.id, light.color

    if not col.errors: print 'File read without errors'
    else:
        print 'Errors:'
        for error in col.errors:
            print ' ', error

if __name__ == '__main__':
    filename = sys.argv[1] if  len(sys.argv) > 1 else 'misc/base.zip'

    # open COLLADA file ignoring some errors in case they appear
    col = collada.Collada(filename, ignore=[collada.DaeUnsupportedError,
                                            collada.DaeBrokenRefError])
    inspectCollada(col)
    