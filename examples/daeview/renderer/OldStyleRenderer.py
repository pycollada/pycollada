#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import

import collada
import numpy
import pyglet
from pyglet.gl import *
import ctypes
from . import glutils


class OldStyleRenderer: 

    def __init__(self, dae, window):
        self.dae = dae
        self.window = window
        # to calculate model boundary
        self.z_max = -100000.0
        self.z_min = 100000.0
        self.textures = {}

        glShadeModel(GL_SMOOTH) # Enable Smooth Shading
        glClearColor(0.0, 0.0, 0.0, 0.5) # Black Background
        glClearDepth(1.0) # Depth Buffer Setup
        glEnable(GL_DEPTH_TEST) # Enables Depth Testing
        glDepthFunc(GL_LEQUAL) # The Type Of Depth Testing To Do
        
        glEnable(GL_MULTISAMPLE);

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glCullFace(GL_BACK)

        glEnable(GL_TEXTURE_2D) # Enable Texture Mapping
        # glEnable(GL_TEXTURE_RECTANGLE_ARB) # Enable Texture Mapping
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        # create one display list
        print('Creating display list...')
        print('It could take some time. Please be patient :-) .')
        self.displist = glGenLists(1)
        # compile the display list, store a triangle in it
        glNewList(self.displist, GL_COMPILE)
        self.drawPrimitives()
        glEndList()
        print('done. Ready to render.')

    def drawPrimitives(self):
        glBegin(GL_TRIANGLES)
        
        if self.dae.scene is not None:
            for geom in self.dae.scene.objects('geometry'):
                for prim in geom.primitives():
                    mat = prim.material
                    diff_color = (GLfloat * 4)(*(0.3,0.3,0.3,0.0))
                    spec_color = None 
                    shininess = None
                    amb_color = None
                    tex_id = None
                    for prop in mat.effect.supported:
                        value = getattr(mat.effect, prop)
                        # it can be a float, a color (tuple) or a Map
                        # ( a texture )
                        if isinstance(value, collada.material.Map):
                            colladaimage = value.sampler.surface.image
                            # Accessing this attribute forces the
                            # loading of the image using PIL if
                            # available. Unless it is already loaded.
                            img = colladaimage.pilimage
                            if img: # can read and PIL available
                                # See if we already have texture for this image
                                if colladaimage.id in self.textures:
                                    tex_id = self.textures[colladaimage.id]
                                else:
                                    # If not - create new texture
                                    try:
                                        # get image meta-data
                                        # (dimensions) and data
                                        (ix, iy, tex_data) = (img.size[0], img.size[1], img.tostring("raw", "RGBA", 0, -1))
                                    except SystemError:
                                        # has no alpha channel,
                                        # synthesize one
                                        (ix, iy, tex_data) = (img.size[0], img.size[1], img.tostring("raw", "RGBX", 0, -1))
                                    # generate a texture ID
                                    tid = GLuint()
                                    glGenTextures(1, ctypes.byref(tid))
                                    tex_id = tid.value
                                    # make it current
                                    glBindTexture(GL_TEXTURE_2D, tex_id)
                                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                                    #glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
                                    # copy the texture into the
                                    # current texture ID
                                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

                                    self.textures[colladaimage.id] = tex_id
                            else:
                                print('  %s = Texture %s: (not available)'%(
                                    prop, colladaimage.id))
                        else:
                            if prop == 'diffuse' and value is not None:
                                diff_color = (GLfloat * 4)(*value)
                            elif prop == 'specular' and value is not None:
                                spec_color = (GLfloat * 4)(*value)
                            elif prop == 'ambient' and value is not None:
                                amb_color = (GLfloat * 4)(*value)
                            elif prop == 'shininess' and value is not None:
                                shininess = value

                    # use primitive-specific ways to get triangles
                    prim_type = type(prim).__name__
                    if prim_type == 'BoundTriangleSet':
                        triangles = prim
                    elif prim_type == 'BoundPolylist':
                        triangles = prim.triangleset()
                    else:
                        print('Unsupported mesh used:', prim_type)
                        triangles = []

                    if tex_id is not None:
                        glBindTexture(GL_TEXTURE_2D, tex_id)
                    else:
                        glBindTexture(GL_TEXTURE_2D, 0)


                    # add triangles to the display list
                    for t in triangles:
                        nidx = 0
                        if tex_id is not None and len(t.texcoords) > 0:
                            texcoords = t.texcoords[0]
                        else:
                            texcoords = None

                        for vidx in t.indices:
                            if diff_color is not None:
                                glMaterialfv(GL_FRONT, GL_DIFFUSE, diff_color)
                            if spec_color is not None:
                                glMaterialfv(GL_FRONT, GL_SPECULAR, spec_color)
                            if amb_color is not None:
                                glMaterialfv(GL_FRONT, GL_AMBIENT, amb_color)
                            if shininess is not None:
                                glMaterialfv(GL_FRONT, GL_SHININESS, (GLfloat * 1)(shininess))

                            # if not t.normals is None:
                            glNormal3fv((GLfloat * 3)(*t.normals[nidx]))
                            if texcoords is not None:
                                glTexCoord2fv((GLfloat * 2)(*texcoords[nidx]))

                            nidx += 1

                            v = prim.vertex[vidx]
                            glVertex3fv((GLfloat * 3)(*v))

                            # calculate max and min Z coordinate
                            if v[2] > self.z_max:
                                self.z_max = v[2]
                            elif v[2] < self.z_min:
                                self.z_min = v[2]
        glutils.getGLError()
        glEnd()


    def render(self, rotate_x, rotate_y, rotate_z):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION) # Select The Projection Matrix
        glLoadIdentity() # Reset The Projection Matrix
        if self.window.height == 0: # Calculate The Aspect Ratio Of The Window
            gluPerspective(100, self.window.width, 1.0, 5000.0)
        else:
            gluPerspective(100, self.window.width / self.window.height, 1.0, 5000.0)
        glMatrixMode(GL_MODELVIEW) # Select The Model View Matrix
        glLoadIdentity()
        z_offset = self.z_min - (self.z_max - self.z_min) * 3
        light_pos = (GLfloat * 3)(100.0, 100.0, 100.0 * -z_offset)
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glTranslatef(0, 0, z_offset)
        glRotatef(rotate_x, 1.0, 0.0, 0.0)
        glRotatef(rotate_y, 0.0, 1.0, 0.0)
        glRotatef(rotate_z, 0.0, 0.0, 1.0)
        
        # draw the display list
        glCallList(self.displist)


    def cleanup(self):
        print('Renderer cleaning up')
        glDeleteLists(self.displist, 1)
