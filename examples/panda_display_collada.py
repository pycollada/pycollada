from math import pi, sin, cos
import numpy
import collada
import sys
import os, os.path
import traceback
import time
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import GeomVertexFormat
from panda3d.core import GeomVertexData
from panda3d.core import GeomVertexWriter
from panda3d.core import GeomTriangles
from panda3d.core import Geom
from panda3d.core import GeomNode
from panda3d.core import PNMImage
from panda3d.core import Texture
from panda3d.core import Filename
from panda3d.core import RenderState
from panda3d.core import TextureAttrib
from panda3d.core import MaterialAttrib
from panda3d.core import Material
from panda3d.core import VBase4, Vec4, Point3
from panda3d.core import AmbientLight, DirectionalLight

if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
    print "Usage: python panda_display_collada.py <file>"
    print "   Loads the given file with pycollada and then tries to display with panda3d"
    sys.exit(1)
    
try:
    col = collada.Collada(sys.argv[1])
except:
    print "Error loading file: "
    print
    traceback.print_exc()
    sys.exit(2)
    
if len(col.errors) > 0:
    print "Warnings when loading file. Quitting."
    print
    sys.exit(3)

format = GeomVertexFormat.getV3n3t2()
node = GeomNode("collada")
myImage = None

for geom in col.scene.objects('geometry'):
    for prim in geom.primitives():
        dataname = geom.original.id + '-' + prim.material.id
        vdata = GeomVertexData(dataname, format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        numtris = 0
        
        if type(prim) is collada.triangleset.BoundTriangleSet:
            for tri in prim.triangles():
                for tri_pt in range(3):
                    vertex.addData3f(tri.vertices[tri_pt][0], tri.vertices[tri_pt][1], tri.vertices[tri_pt][2])
                    normal.addData3f(tri.normals[tri_pt][0], tri.normals[tri_pt][1], tri.normals[tri_pt][2])
                    if len(prim._texcoordset) > 0:
                        texcoord.addData2f(tri.texcoords[0][tri_pt][0], tri.texcoords[0][tri_pt][1])
                numtris+=1
        elif type(prim) is collada.polylist.BoundPolygonList:
            
            for poly in prim.polygons():
            
                tris = poly.triangulate()
    
                for tri in tris:
                    for tri_pt in range(3):
                        vertex.addData3f(tri.vertices[tri_pt][0], tri.vertices[tri_pt][1], tri.vertices[tri_pt][2])
                        normal.addData3f(tri.normals[tri_pt][0], tri.normals[tri_pt][1], tri.normals[tri_pt][2])
                        if len(prim._texcoordset) > 0:
                            texcoord.addData2f(tri.texcoords[0][tri_pt][0], tri.texcoords[0][tri_pt][1])
                    numtris+=1

        else:
            print "Error: Unsupported primitive type. Exiting."
            sys.exit(2)
        
        gprim = GeomTriangles(Geom.UHStatic)
        for i in range(numtris):
            gprim.addVertices(i*3, i*3+1, i*3+2)
            gprim.closePrimitive()
            
        pgeom = Geom(vdata)
        pgeom.addPrimitive(gprim)
        
        state = RenderState.makeFullDefault()
        
        emission = None
        ambient = None
        diffuse = None
        specular = None
        shininess = None
        reflection = None
        reflectivity = None
        
        for prop in prim.material.supported:
            value = getattr(prim.material, prop)
            
            if value is None:
                continue
            
            if type(value) is tuple:
                val4 = value[3] if len(value) > 3 else 1.0
                value = VBase4(value[0], value[1], value[2], val4)
            
            if isinstance(value, collada.material.Map):
                texture_file = value.sampler.surface.image.path
                if not texture_file is None:
                    (root, leaf) = os.path.split(sys.argv[1])
                    tex_absolute = os.path.join(root, texture_file)
                    myImage = PNMImage()
                    myImage.read(Filename(tex_absolute))
                    myTexture = Texture(texture_file)
                    myTexture.load(myImage)
                    state = state.addAttrib(TextureAttrib.make(myTexture))
            elif prop == 'emission':
                emission = value
            elif prop == 'ambient':
                ambient = value
            elif prop == 'diffuse':
                diffuse = value
            elif prop == 'specular':
                specular = value
            elif prop == 'shininess':
                shininess = value
            elif prop == 'reflective':
                reflective = value
            elif prop == 'reflectivity':
                reflectivity = value
            elif prop == 'transparent':
                pass
            elif prop == 'transparency':
                pass
            else:
                raise
        
        mat = Material()
        
        if not emission is None:
            mat.setEmission(emission)
        if not ambient is None:
            mat.setAmbient(ambient)
        if not diffuse is None:
            mat.setDiffuse(diffuse)
        if not specular is None:
            mat.setSpecular(specular)
        if not shininess is None:
            mat.setShininess(shininess)
        
        state = state.addAttrib(MaterialAttrib.make(mat))
        node.addGeom(pgeom, state)


p3dApp = ShowBase()

boundingSphere = node.getBounds()
scale = 5.0 / boundingSphere.getRadius()

nodePath = render.attachNewNode(node)

nodePath.setScale(scale, scale, scale)
boundingSphere = nodePath.getBounds()
nodePath.setPos(-1 * boundingSphere.getCenter().getX(),
                -1 * boundingSphere.getCenter().getY(),
                -1 * boundingSphere.getCenter().getZ())
nodePath.setHpr(0,0,0)

# Define a procedure to move the camera.
def spinCameraTask(task):
    speed = 5.0
    curSpot = task.time % speed
    angleDegrees = (curSpot / speed) * 360
    angleRadians = angleDegrees * (pi / 180.0) 
    camera.setPos(20.0 * sin(angleRadians), -20.0 * cos(angleRadians), 2.5)
    camera.lookAt(0.0, 0.0, 0.0)
    return Task.cont
 
# Add the procedure to the task manager.
p3dApp.taskMgr.add(spinCameraTask, "SpinCameraTask")

base.setBackgroundColor(0.8,0.8,0.8)
base.disableMouse()

# Create Ambient Light
ambientLight = AmbientLight('ambientLight')
ambientLight.setColor(Vec4(0.1, 0.1, 0.1, 1))
ambientLightNP = render.attachNewNode(ambientLight)
render.setLight(ambientLightNP)

directionalPoints = [(10,0,0), (-10,0,0),
                     (0,-10,0), (0,10,0),
                     (0, 0, -10), (0,0,10)]

for pt in directionalPoints:
    directionalLight = DirectionalLight('directionalLight')
    directionalLight.setColor(Vec4(0.4, 0.4, 0.4, 1))
    directionalLightNP = render.attachNewNode(directionalLight)
    directionalLightNP.setPos(pt[0], pt[1], pt[2])
    directionalLightNP.lookAt(0,0,0)
    render.setLight(directionalLightNP)

p3dApp.run()
