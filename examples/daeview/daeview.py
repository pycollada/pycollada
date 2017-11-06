#!/usr/bin/env python
import collada
import sys
import os
import renderer

import pyglet
from pyglet.gl import *


try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4,
                    depth_size=16, double_buffer=True)
    window = pyglet.window.Window(resizable=False, config=config, vsync=True)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=False)

window.rotate_x  = 0.0
window.rotate_y = 0.0
window.rotate_z = 0.0


@window.event
def on_draw():
    daerender.render(window.rotate_x, window.rotate_y, window.rotate_z)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if abs(dx) > 2:
        if dx > 0:
            window.rotate_y += 2
        else:
            window.rotate_y -= 2
		
    if abs(dy) > 1:
        if dy > 0:
            window.rotate_x -= 2
        else:
            window.rotate_x += 2

    
@window.event
def on_resize(width, height):
    if height==0: height=1
    # Override the default on_resize handler to create a 3D projection
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), .1, 1000.)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED


if __name__ == '__main__':
    filename = sys.argv[1] if  len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'data', 'cockpit.zip')

    # open COLLADA file ignoring some errors in case they appear
    collada_file = collada.Collada(filename, ignore=[collada.DaeUnsupportedError,
                                            collada.DaeBrokenRefError])

    daerender = renderer.GLSLRenderer(collada_file)
    #daerender = renderer.OldStyleRenderer(collada_file, window)
	
    window.width = 1024
    window.height = 768
    
    pyglet.app.run()

    daerender.cleanup()
