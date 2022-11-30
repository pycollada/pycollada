from __future__ import print_function
from __future__ import absolute_import

import pyglet
from pyglet.gl import *
import ctypes


def VecF(*args):
    """Simple function to create ctypes arrays of floats"""
    return (GLfloat * len(args))(*args)


def getOpenGLVersion():
    """Get the OpenGL minor and major version number"""
    versionString = glGetString(GL_VERSION)
    return ctypes.cast(versionString, ctypes.c_char_p).value


def getGLError():
    e = glGetError()
    if e != 0:
        errstr = gluErrorString(e)
        print('GL ERROR:', errstr)
        return errstr
    else:
        return None
