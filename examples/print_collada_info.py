#!/usr/bin/env python

import collada
import numpy
import sys

def inspectGeometry(obj):
    """Display contents of a geometry object found in the scene."""
    avgpoint = numpy.zeros( (3,), dtype=numpy.float32 )
    avgtexcoord = numpy.zeros( (2,), dtype=numpy.float32 )
    num = 0
    numuv = 0
    materials = set()
    for prim in obj.primitives():
        materials.add( prim.material )
        # iterate triangles to sum up the points for the average
        # we could also use the prim.vertex attribute which is a
        # numpy array of all the vertices in the primitive
        for tri in prim.triangles():
            avgpoint += tri.vertices[0] + tri.vertices[1] + tri.vertices[2]
            if tri.texcoords:
                # primitives can have more than one texcoord channel
                # we average the first one (tri.texcoords[0])
                avgtexcoord += (tri.texcoords[0][0] + tri.texcoords[0][1] + 
                                tri.texcoords[0][2])
                numuv += 3
            num += 3
    avgpoint /= float(num)
    if numuv:
        avgtexcoord /= float(numuv)
        print '    Geometry %s: %d primitives, avg point %s avgUV %s'%(
                   obj.original.id, len(obj), str(avgpoint), str(avgtexcoord))
    else:
        print '    Geometry %s: %d primitives, avg point %s'%(
                   obj.original.id, len(obj), str(avgpoint))
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
    print '  Geometry:'
    for geom in col.scene.objects('geometry'):
        inspectGeometry( geom )
    print '  Cameras:'
    for cam in col.scene.objects('camera'):
        print '    Camera %s: position '%cam.original.id, cam.position

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
    