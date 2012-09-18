import pyglet
from pyglet.gl import *
import ctypes


def VecF(*args):
    """Simple function to create ctypes arrays of floats"""
    return (GLfloat * len(args))(*args)

def getOpenGLVersion():
    """Get the OpenGL minor and major version number"""
    versionString = glGetString(GL_VERSION)
    return cast(versionString, c_char_p).value
