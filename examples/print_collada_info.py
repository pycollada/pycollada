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
    avgpoint = numpy.zeros( (3,), dtype=numpy.float32 )
    num = 0
    numuv = 0
    materials = set()
    for prim in obj.primitives():
        materials.add( prim.material )
        # iterate shapes to sum up the points for the average
        # we could also use the prim.vertex attribute which is a
        # numpy array of all the vertices in the primitive
        for shape in prim.shapes():
            for vertex in shape.vertices:
                avgpoint += vertex
                num += 1
    avgpoint /= float(num)
    print '    Geometry (id=%s): %d primitives, avg point %s'%(
               obj.original.id, len(obj), str(avgpoint))
    for prim in obj.primitives():
        print '        Primitive (type=%s): len=%d' % (type(prim).__name__, len(prim))
    for mat in materials:
        if mat: inspectMaterial( mat )

def inspectMaterial(mat):
    """Display material contents."""
    print '        Material %s: shading %s'%(mat.id, mat.shadingtype)
    for prop in mat.supported:
        value = getattr(mat, prop)
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
    for geom in col.scene.objects('geometry'):
        inspectGeometry( geom )
    print '  Controllers:'
    for controller in col.scene.objects('controller'):
        inspectController( controller )
    print '  Cameras:'
    for cam in col.scene.objects('camera'):
        print '    Camera %s: position '%cam.original.id, cam.position
    print '  Lights:'
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
    