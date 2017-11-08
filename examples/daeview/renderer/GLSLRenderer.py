#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import

import collada
import numpy

import pyglet
from pyglet.gl import *

import ctypes

from . import glutils
from .glutils import VecF
from . import shader
from .shader import Shader
from . import shaders


class GLSLRenderer: 

    def __init__(self, dae):
        self.dae = dae
        # To calculate model boundary along Z axis
        self.z_max = -100000.0
        self.z_min = 100000.0
        self.textures = {}
        self.shaders = {}
        self.batch_list = []

        # Initialize OpenGL
        glClearColor(0.0, 0.0, 0.0, 0.5) # Black Background
        glEnable(GL_DEPTH_TEST) # Enables Depth Testing
        glEnable(GL_CULL_FACE)
        glEnable(GL_MULTISAMPLE);

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_LIGHTING)

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, VecF(0.9, 0.9, 0.9, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, VecF(1.0, 1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, VecF(0.3, 0.3, 0.3, 1.0))

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, VecF(0.1, 0.1, 0.1, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, VecF(0.1, 0.1, 0.1, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50)

        print('Running with OpenGL version:', glutils.getOpenGLVersion())
        print('Initializing shaders...')
        #(vert, frag) = shaders.ADSPhong
        (vert, frag) = shaders.simplePhong
        prog = Shader(vert, frag)
        print('  phong')
        self.shaders['phong'] = prog
        (vert, frag) = shaders.pointLightDiff
        prog = Shader(vert, frag)
        self.shaders['lambert'] = prog
        print('  lambert')
        self.shaders['blinn'] = prog
        print('  blinn')
        (vert, frag) = shaders.flatShader
        prog = Shader(vert, frag)
        self.shaders['constant'] = prog
        print('  constant')
        (vert, frag) = shaders.texturePhong
        prog = Shader(vert, frag)
        self.shaders['texture'] = prog
        print('  texture')
        print('  done.')

        print('Creating GL buffer objects for geometry...')
        if self.dae.scene is not None:
            for geom in self.dae.scene.objects('geometry'):
                for prim in geom.primitives():
                    mat = prim.material
                    diff_color = VecF(0.3,0.3,0.3,1.0)
                    spec_color = None 
                    shininess = None
                    amb_color = None
                    tex_id = None
                    shader_prog = self.shaders[mat.effect.shadingtype]
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
                                shader_prog = self.shaders['texture']
                                # See if we already have texture for this image
                                if colladaimage.id in self.textures:
                                    tex_id = self.textures[colladaimage.id]
                                else:
                                    # If not - create new texture
                                    try:
                                        # get image meta-data
                                        # (dimensions) and data
                                        (ix, iy, tex_data) = (img.size[0], img.size[1], img.tobytes("raw", "RGBA", 0, -1))
                                    except (SystemError, ValueError):
                                        # has no alpha channel,
                                        # synthesize one
                                        (ix, iy, tex_data) = (img.size[0], img.size[1], img.tobytes("raw", "RGBX", 0, -1))
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
                                    # copy the texture into the
                                    # current texture ID
                                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

                                    self.textures[colladaimage.id] = tex_id
                            else:
                                print('  %s = Texture %s: (not available)'%(
                                    prop, colladaimage.id))
                        else:
                            if prop == 'diffuse' and value is not None:
                                diff_color = value
                            elif prop == 'specular' and value is not None:
                                spec_color = value
                            elif prop == 'ambient' and value is not None:
                                amb_color = value
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
                        triangles = None

                    if triangles is not None:
                        triangles.generateNormals()
                        # We will need flat lists for VBO (batch) initialization
                        vertices = triangles.vertex.flatten().tolist()
                        batch_len = len(vertices)//3
                        indices = triangles.vertex_index.flatten().tolist()
                        normals = triangles.normal.flatten().tolist()

                        batch = pyglet.graphics.Batch()

                        # Track maximum and minimum Z coordinates
                        # (every third element) in the flattened
                        # vertex list
                        ma = max(vertices[2::3])
                        if ma > self.z_max:
                            self.z_max = ma

                        mi = min(vertices[2::3])
                        if mi < self.z_min:
                            self.z_min = mi

                        if tex_id is not None:

                            # This is probably the most inefficient
                            # way to get correct texture coordinate
                            # list (uv). I am sure that I just do not
                            # understand enough how texture
                            # coordinates and corresponding indexes
                            # are related to the vertices and vertex
                            # indicies here, but this is what I found
                            # to work. Feel free to improve the way
                            # texture coordinates (uv) are collected
                            # for batch.add_indexed() invocation.
                            uv = [[0.0,0.0]] * batch_len
                            for t in triangles:
                                nidx = 0
                                texcoords = t.texcoords[0]
                                for vidx in t.indices:
                                    uv[vidx] = texcoords[nidx].tolist()
                                    nidx += 1
                            # Flatten the uv list
                            uv = [item for sublist in uv for item in sublist]

                            # Create textured batch
                            batch.add_indexed(batch_len, 
                                              GL_TRIANGLES,
                                              None,
                                              indices,
                                              ('v3f/static', vertices),
                                              ('n3f/static', normals),
                                              ('t2f/static', uv))
                        else:
                            # Create colored batch
                            batch.add_indexed(batch_len, 
                                              GL_TRIANGLES,
                                              None,
                                              indices,
                                              ('v3f/static', vertices),
                                              ('n3f/static', normals))

                        # Append the batch with supplimentary
                        # information to the batch list
                        self.batch_list.append(
                            (batch, shader_prog, tex_id, diff_color, 
                             spec_color, amb_color, shininess))
        print('done. Ready to render.')

    def render(self, rotate_x, rotate_y, rotate_z):
        """Render batches created during class initialization"""

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Place the light far behind our object
        z_offset = self.z_min - (self.z_max - self.z_min) * 3
        light_pos = VecF(100.0, 100.0, 10.0 * -z_offset)
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        
        # Move the object deeper to the screen and rotate
        glTranslatef(0, 0, z_offset)
        glRotatef(rotate_x, 1.0, 0.0, 0.0)
        glRotatef(rotate_y, 0.0, 1.0, 0.0)
        glRotatef(rotate_z, 0.0, 0.0, 1.0)

        prev_shader_prog = None
        # Draw batches (VBOs)
        for (batch, shader_prog, tex_id, diff_color, spec_color, amb_color, shininess) in self.batch_list:
            # Optimization to not make unnecessary bind/unbind for the
            # shader. Most of the time there will be same shaders for
            # geometries.
            if shader_prog != prev_shader_prog:
                if prev_shader_prog is not None:
                    prev_shader_prog.unbind()
                prev_shader_prog = shader_prog
                shader_prog.bind()

            if diff_color is not None:
                shader_prog.uniformf('diffuse', *diff_color)
            if spec_color is not None:
                shader_prog.uniformf('specular', *spec_color)
            if amb_color is not None:
                shader_prog.uniformf('ambient', *amb_color)
            if shininess is not None:
                shader_prog.uniformf('shininess', shininess)

            if tex_id is not None:
                # We assume that the shader here is 'texture'
                glActiveTexture(GL_TEXTURE0)
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                shader_prog.uniformi('my_color_texture[0]', 0)

            batch.draw()
        if prev_shader_prog is not None:
            prev_shader_prog.unbind()


    def cleanup(self):
        print('Renderer cleaning up')
