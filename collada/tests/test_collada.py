import unittest2
import collada
from lxml.etree import fromstring, tostring
from StringIO import StringIO
import numpy
import os

class TestCollada(unittest2.TestCase):

    def setUp(self):
        self.dummy = collada.Collada()
        self.datadir = os.path.join(os.path.dirname(os.path.realpath( __file__ )), "data")

    def test_collada_duck_tris(self):
        f = os.path.join(self.datadir, "duck_triangles.dae")
        mesh = collada.Collada(f)
        self.assertEqual(mesh.scene.id, 'VisualSceneNode')
        self.assertIn('LOD3spShape-lib', mesh.geometries)
        self.assertIn('directionalLightShape1-lib', mesh.lights)
        self.assertIn('cameraShape1', mesh.cameras)
        self.assertIn('file2', mesh.images)
        self.assertIn('blinn3-fx', mesh.effects)
        self.assertIn('blinn3', mesh.materials)
        self.assertEqual(len(mesh.nodes), 0)
        self.assertIn('VisualSceneNode', mesh.scenes)
        
        self.assertIsNotNone(str(list(mesh.scene.objects('geometry'))))
        self.assertIsNotNone(str(list(mesh.scene.objects('light'))))
        self.assertIsNotNone(str(list(mesh.scene.objects('camera'))))
                
    def test_collada_duck_poly(self):
        f = os.path.join(self.datadir, "duck_polylist.dae")
        mesh = collada.Collada(f)
        self.assertEqual(mesh.scene.id, 'VisualSceneNode')
        self.assertIn('LOD3spShape-lib', mesh.geometries)
        self.assertIn('directionalLightShape1-lib', mesh.lights)
        self.assertIn('cameraShape1', mesh.cameras)
        self.assertIn('file2', mesh.images)
        self.assertIn('blinn3-fx', mesh.effects)
        self.assertIn('blinn3', mesh.materials)
        self.assertEqual(len(mesh.nodes), 0)
        self.assertIn('VisualSceneNode', mesh.scenes)
        
    def test_collada_duck_zip(self):
        f = os.path.join(self.datadir, "duck.zip")
        mesh = collada.Collada(f)
        self.assertEqual(mesh.scene.id, 'VisualSceneNode')
        self.assertIn('LOD3spShape-lib', mesh.geometries)
        self.assertIn('directionalLightShape1-lib', mesh.lights)
        self.assertIn('cameraShape1', mesh.cameras)
        self.assertIn('file2', mesh.images)
        self.assertIn('blinn3-fx', mesh.effects)
        self.assertIn('blinn3', mesh.materials)
        self.assertEqual(len(mesh.nodes), 0)
        self.assertIn('VisualSceneNode', mesh.scenes)

    def test_collada_saving(self):       
        mesh = collada.Collada()

        self.assertEqual(len(mesh.geometries), 0)
        self.assertEqual(len(mesh.controllers), 0)
        self.assertEqual(len(mesh.lights), 0)
        self.assertEqual(len(mesh.cameras), 0)
        self.assertEqual(len(mesh.images), 0)
        self.assertEqual(len(mesh.effects), 0)
        self.assertEqual(len(mesh.materials), 0)
        self.assertEqual(len(mesh.nodes), 0)
        self.assertEqual(len(mesh.scenes), 0)
        self.assertEqual(mesh.scene, None)
        self.assertIsNotNone(str(mesh))

        floatsource = collada.source.FloatSource("myfloatsource", numpy.array([0.1,0.2,0.3]), ('X', 'Y', 'Z'))
        geometry1 = collada.geometry.Geometry(mesh, "geometry1", "mygeometry1", {"myfloatsource":floatsource})
        mesh.geometries.append(geometry1)
        
        linefloats = [1,1,-1, 1,-1,-1, -1,-0.9999998,-1, -0.9999997,1,-1, 1,0.9999995,1, 0.9999994,-1.000001,1]
        linefloatsrc = collada.source.FloatSource("mylinevertsource", numpy.array(linefloats), ('X', 'Y', 'Z'))
        geometry2 = collada.geometry.Geometry(mesh, "geometry2", "mygeometry2", [linefloatsrc])
        input_list = collada.source.InputList()
        input_list.addInput(0, 'VERTEX', "#mylinevertsource")
        indices = numpy.array([0,1, 1,2, 2,3, 3,4, 4,5])
        lineset1 = geometry2.createLineSet(indices, input_list, "mymaterial2")
        geometry2.primitives.append(lineset1)
        mesh.geometries.append(geometry2)
        
        ambientlight = collada.light.AmbientLight("myambientlight", (1,1,1))
        pointlight = collada.light.PointLight("mypointlight", (1,1,1))
        mesh.lights.append(ambientlight)
        mesh.lights.append(pointlight)
        
        camera1 = collada.camera.Camera("mycam1", 45.0, 0.01, 1000.0)
        camera2 = collada.camera.Camera("mycam2", 45.0, 0.01, 1000.0)
        mesh.cameras.append(camera1)
        mesh.cameras.append(camera2)
        
        cimage1 = collada.material.CImage("mycimage1", "./whatever.tga", mesh)
        cimage2 = collada.material.CImage("mycimage2", "./whatever.tga", mesh)
        mesh.images.append(cimage1)
        mesh.images.append(cimage2)
        
        effect1 = collada.material.Effect("myeffect1", [], "phong")
        effect2 = collada.material.Effect("myeffect2", [], "phong")
        mesh.effects.append(effect1)
        mesh.effects.append(effect2)
        
        mat1 = collada.material.Material("mymaterial1", "mymat1", effect1)
        mat2 = collada.material.Material("mymaterial2", "mymat2", effect2)
        mesh.materials.append(mat1)
        mesh.materials.append(mat2)
        
        rotate = collada.scene.RotateTransform(0.1, 0.2, 0.3, 90)
        scale = collada.scene.ScaleTransform(0.1, 0.2, 0.3)
        mynode1 = collada.scene.Node('mynode1', children=[], transforms=[rotate, scale])
        mynode2 = collada.scene.Node('mynode2', children=[], transforms=[])
        mesh.nodes.append(mynode1)
        mesh.nodes.append(mynode2)
        
        geomnode = collada.scene.GeometryNode(geometry2)
        mynode3 = collada.scene.Node('mynode3', children=[geomnode], transforms=[])
        mynode4 = collada.scene.Node('mynode4', children=[], transforms=[])
        scene1 = collada.scene.Scene('myscene1', [mynode3])
        scene2 = collada.scene.Scene('myscene2', [mynode4])
        mesh.scenes.append(scene1)
        mesh.scenes.append(scene2)
        
        mesh.scene = scene1
        
        out = StringIO()
        mesh.write(out)
        
        toload = StringIO(out.getvalue())
        
        loaded_mesh = collada.Collada(toload)
        self.assertEqual(len(loaded_mesh.geometries), 2)
        self.assertEqual(len(loaded_mesh.controllers), 0)
        self.assertEqual(len(loaded_mesh.lights), 2)
        self.assertEqual(len(loaded_mesh.cameras), 2)
        self.assertEqual(len(loaded_mesh.images), 2)
        self.assertEqual(len(loaded_mesh.effects), 2)
        self.assertEqual(len(loaded_mesh.materials), 2)
        self.assertEqual(len(loaded_mesh.nodes), 2)
        self.assertEqual(len(loaded_mesh.scenes), 2)
        self.assertEqual(loaded_mesh.scene.id, scene1.id)
        
        self.assertIn('geometry1', loaded_mesh.geometries)
        self.assertIn('geometry2', loaded_mesh.geometries)
        self.assertIn('mypointlight', loaded_mesh.lights)
        self.assertIn('myambientlight', loaded_mesh.lights)
        self.assertIn('mycam1', loaded_mesh.cameras)
        self.assertIn('mycam2', loaded_mesh.cameras)
        self.assertIn('mycimage1', loaded_mesh.images)
        self.assertIn('mycimage2', loaded_mesh.images)
        self.assertIn('myeffect1', loaded_mesh.effects)
        self.assertIn('myeffect2', loaded_mesh.effects)
        self.assertIn('mymaterial1', loaded_mesh.materials)
        self.assertIn('mymaterial2', loaded_mesh.materials)
        self.assertIn('mynode1', loaded_mesh.nodes)
        self.assertIn('mynode2', loaded_mesh.nodes)
        self.assertIn('myscene1', loaded_mesh.scenes)
        self.assertIn('myscene2', loaded_mesh.scenes)
        
        geometry3 = collada.geometry.Geometry(mesh, "geometry3", "mygeometry3", [linefloatsrc])
        loaded_mesh.geometries.pop(0)
        loaded_mesh.geometries.append(geometry3)
        
        dirlight = collada.light.DirectionalLight("mydirlight", (1,1,1))
        loaded_mesh.lights.pop(0)
        loaded_mesh.lights.append(dirlight)
        
        camera3 = collada.camera.Camera("mycam3", 45.0, 0.01, 1000.0)
        loaded_mesh.cameras.pop(0)
        loaded_mesh.cameras.append(camera3)
        
        cimage3 = collada.material.CImage("mycimage3", "./whatever.tga", loaded_mesh)
        loaded_mesh.images.pop(0)
        loaded_mesh.images.append(cimage3)
        
        effect3 = collada.material.Effect("myeffect3", [], "phong")
        loaded_mesh.effects.pop(0)
        loaded_mesh.effects.append(effect3)
        
        mat3 = collada.material.Material("mymaterial3", "mymat3", effect3)
        loaded_mesh.materials.pop(0)
        loaded_mesh.materials.append(mat3)
        
        mynode5 = collada.scene.Node('mynode5', children=[], transforms=[])
        loaded_mesh.nodes.pop(0)
        loaded_mesh.nodes.append(mynode5)
        
        mynode6 = collada.scene.Node('mynode6', children=[], transforms=[])
        scene3 = collada.scene.Scene('myscene3', [mynode6])
        loaded_mesh.scenes.pop(0)
        loaded_mesh.scenes.append(scene3)
        
        loaded_mesh.scene = scene3
        
        loaded_mesh.save()
        
        strdata = tostring(loaded_mesh.xmlnode)
        indata = StringIO(strdata)
        loaded_mesh2 = collada.Collada(indata)
        
        self.assertEqual(loaded_mesh2.scene.id, scene3.id)
        self.assertIn('geometry3', loaded_mesh2.geometries)
        self.assertIn('geometry2', loaded_mesh2.geometries)
        self.assertIn('mydirlight', loaded_mesh2.lights)
        self.assertIn('mypointlight', loaded_mesh2.lights)
        self.assertIn('mycam3', loaded_mesh2.cameras)
        self.assertIn('mycam2', loaded_mesh2.cameras)
        self.assertIn('mycimage3', loaded_mesh2.images)
        self.assertIn('mycimage2', loaded_mesh2.images)
        self.assertIn('myeffect3', loaded_mesh2.effects)
        self.assertIn('myeffect2', loaded_mesh2.effects)
        self.assertIn('mymaterial3', loaded_mesh2.materials)
        self.assertIn('mymaterial2', loaded_mesh2.materials)
        self.assertIn('mynode5', loaded_mesh2.nodes)
        self.assertIn('mynode2', loaded_mesh2.nodes)
        self.assertIn('myscene3', loaded_mesh2.scenes)
        self.assertIn('myscene2', loaded_mesh2.scenes)

if __name__ == '__main__':
    unittest2.main()
