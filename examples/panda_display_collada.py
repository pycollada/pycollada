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
from panda3d.core import Material, SparseArray
from panda3d.core import VBase4, Vec4, Point3, Mat4
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import Character, PartGroup, CharacterJoint
from panda3d.core import TransformBlend, TransformBlendTable, JointVertexTransform
from panda3d.core import GeomVertexAnimationSpec, GeomVertexArrayFormat, InternalName
from panda3d.core import AnimBundle, AnimGroup, AnimChannelMatrixXfmTable
from panda3d.core import PTAFloat, CPTAFloat, AnimBundleNode, NodePath
from direct.actor.Actor import Actor

if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
    print "Usage: python panda_display_collada.py <file>"
    print "   Loads the given file with pycollada and then tries to display with panda3d"
    sys.exit(1)

def getStateFromMaterial(prim_material):
    state = RenderState.makeFullDefault()
    
    emission = None
    ambient = None
    diffuse = None
    specular = None
    shininess = None
    reflection = None
    reflectivity = None
    
    for prop in prim_material.supported:
        value = getattr(prim_material, prop)
        
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
    return state


start_time = time.time()
    
try:
    col = collada.Collada(sys.argv[1])
except:
    print "Error loading file: "
    print
    traceback.print_exc()
    sys.exit(2)

collada_time = time.time()

if len(col.errors) > 0:
    print "Warnings when loading file. Quitting."
    print
    sys.exit(3)

p3dApp = ShowBase()

globNode = GeomNode("collada")
nodePath = render.attachNewNode(globNode)

for geom in col.scene.objects('geometry'):
    for prim in geom.primitives():
        
        format = GeomVertexFormat.getV3n3t2()
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
                for tri in poly.triangles():
                    for tri_pt in range(3):
                        vertex.addData3f(tri.vertices[tri_pt][0], tri.vertices[tri_pt][1], tri.vertices[tri_pt][2])
                        normal.addData3f(tri.normals[tri_pt][0], tri.normals[tri_pt][1], tri.normals[tri_pt][2])
                        if len(prim._texcoordset) > 0:
                            texcoord.addData2f(tri.texcoords[0][tri_pt][0], tri.texcoords[0][tri_pt][1])
                    numtris+=1

        else:
            sys.exit("Error: Unsupported primitive type. Exiting.")
        
        gprim = GeomTriangles(Geom.UHStatic)
        for i in range(numtris):
            gprim.addVertices(i*3, i*3+1, i*3+2)
            gprim.closePrimitive()
            
        pgeom = Geom(vdata)
        pgeom.addPrimitive(gprim)
        
        render_state = getStateFromMaterial(prim.material)
        node = GeomNode("primitive")
        node.addGeom(pgeom, render_state)
        nodePath.attachNewNode(node)

for controller in col.scene.objects('controller'):
    for controlled_prim in controller.primitives():
        if type(controlled_prim) is collada.controller.BoundSkinPrimitive:
            ch = Character('simplechar')
            bundle = ch.getBundle(0)
            skeleton = PartGroup(bundle, '<skeleton>')

            character_joints = {}
            for (name, joint_matrix) in controller.joint_matrices.iteritems():
                joint_matrix.shape = (-1)
                character_joints[name] = CharacterJoint(ch, bundle, skeleton, name, Mat4(*joint_matrix)) 
            
            tbtable = TransformBlendTable()
            
            for influence in controller.index:
                blend = TransformBlend()
                for (joint_index, weight_index) in influence:
                    char_joint = character_joints[controller.getJoint(joint_index)]
                    weight = controller.getWeight(weight_index)[0]
                    blend.addTransform(JointVertexTransform(char_joint), weight)
                tbtable.addBlend(blend)
                
            array = GeomVertexArrayFormat()
            array.addColumn(InternalName.make('vertex'), 3, Geom.NTFloat32, Geom.CPoint)
            array.addColumn(InternalName.make('normal'), 3, Geom.NTFloat32, Geom.CPoint)
            array.addColumn(InternalName.make('texcoord'), 2, Geom.NTFloat32, Geom.CTexcoord)
            blendarr = GeomVertexArrayFormat()
            blendarr.addColumn(InternalName.make('transform_blend'), 1, Geom.NTUint16, Geom.CIndex)
            
            format = GeomVertexFormat()
            format.addArray(array)
            format.addArray(blendarr)
            aspec = GeomVertexAnimationSpec()
            aspec.setPanda()
            format.setAnimation(aspec)
            format = GeomVertexFormat.registerFormat(format)
            
            dataname = controller.id + '-' + controlled_prim.primitive.material.id
            vdata = GeomVertexData(dataname, format, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            normal = GeomVertexWriter(vdata, 'normal')
            texcoord = GeomVertexWriter(vdata, 'texcoord')
            transform = GeomVertexWriter(vdata, 'transform_blend') 
            
            numtris = 0
            if type(controlled_prim.primitive) is collada.polylist.BoundPolygonList:
                for poly in controlled_prim.primitive.polygons():
                    for tri in poly.triangles():
                        for tri_pt in range(3):
                            vertex.addData3f(tri.vertices[tri_pt][0], tri.vertices[tri_pt][1], tri.vertices[tri_pt][2])
                            normal.addData3f(tri.normals[tri_pt][0], tri.normals[tri_pt][1], tri.normals[tri_pt][2])
                            if len(controlled_prim.primitive._texcoordset) > 0:
                                texcoord.addData2f(tri.texcoords[0][tri_pt][0], tri.texcoords[0][tri_pt][1])
                            transform.addData1i(tri.indices[tri_pt])
                        numtris+=1
            elif type(controlled_prim.primitive) is collada.triangleset.BoundTriangleSet:
                for tri in controlled_prim.primitive.triangles():
                    for tri_pt in range(3):
                        vertex.addData3f(tri.vertices[tri_pt][0], tri.vertices[tri_pt][1], tri.vertices[tri_pt][2])
                        normal.addData3f(tri.normals[tri_pt][0], tri.normals[tri_pt][1], tri.normals[tri_pt][2])
                        if len(controlled_prim.primitive._texcoordset) > 0:
                            texcoord.addData2f(tri.texcoords[0][tri_pt][0], tri.texcoords[0][tri_pt][1])
                        transform.addData1i(tri.indices[tri_pt])
                    numtris+=1
                        
            tbtable.setRows(SparseArray.lowerOn(vdata.getNumRows())) 
            
            gprim = GeomTriangles(Geom.UHStatic)
            for i in range(numtris):
                gprim.addVertices(i*3, i*3+1, i*3+2)
                gprim.closePrimitive()
                
            pgeom = Geom(vdata)
            pgeom.addPrimitive(gprim)
            
            render_state = getStateFromMaterial(controlled_prim.primitive.material)
            control_node = GeomNode("ctrlnode")
            control_node.addGeom(pgeom, render_state)
            ch.addChild(control_node)
        
            bundle = AnimBundle('simplechar', 5.0, 2)
            skeleton = AnimGroup(bundle, '<skeleton>')
            root = AnimChannelMatrixXfmTable(skeleton, 'root')
            
            hjoint = AnimChannelMatrixXfmTable(root, 'joint1') 
            table = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11] 
            data = PTAFloat.emptyArray(len(table)) 
            for i in range(len(table)): 
                data.setElement(i, table[i]) 
            hjoint.setTable(ord('i'), CPTAFloat(data)) 
            
            vjoint = AnimChannelMatrixXfmTable(hjoint, 'joint2') 
            table = [10, 9, 8, 7, 6, 5, 6, 7, 8, 9] 
            data = PTAFloat.emptyArray(len(table)) 
            for i in range(len(table)): 
                data.setElement(i, table[i]) 
            vjoint.setTable(ord('j'), CPTAFloat(data)) 

            wiggle = AnimBundleNode('wiggle', bundle)

            np = NodePath(ch) 
            anim = NodePath(wiggle) 
            a = Actor(np, {'simplechar' : anim}) 
            a.reparentTo(nodePath)
            #a.setPos(0, 0, 0)
            a.loop('simplechar')
        
        else:
            sys.exit("Error: unsupported controller type")

boundingSphere = nodePath.getBounds()
scale = 5.0 / boundingSphere.getRadius()

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
    base.camera.setPos(25.0 * sin(angleRadians), -25.0 * cos(angleRadians), 0)
    base.camera.lookAt(0.0, 0.0, 0.0)
    return Task.cont

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

end_time = time.time()
print "Loaded in %.3f seconds" % (end_time-start_time)
print "Collada file loaded in %.3f seconds" % (collada_time-start_time)

p3dApp.run()
