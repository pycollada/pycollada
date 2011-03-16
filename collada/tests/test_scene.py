import unittest2
import collada
import StringIO
import numpy
from lxml.etree import fromstring, tostring

class TestScene(unittest2.TestCase):

    def setUp(self):
        self.dummy_collada_text = """
        <COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
        </COLLADA>
        """
        self.dummy = collada.Collada(StringIO.StringIO(self.dummy_collada_text))
        
        self.yourcam = collada.camera.Camera("yourcam", 45.0, 0.01, 1000.0)
        self.dummy.cameraById['yourcam'] = self.yourcam
        
        self.yoursunlight = collada.light.SunLight("yoursunlight", (1,1,1))
        self.dummy.lightById['yoursunlight'] = self.yoursunlight

    def test_scene_light_node_saving(self):
        sunlight = collada.light.SunLight("mysunlight", (1,1,1))
        lightnode = collada.scene.LightNode(sunlight)
        bindtest = list(lightnode.objects('light'))
        self.assertEqual(lightnode.light, sunlight)
        self.assertEqual(len(bindtest), 1)
        self.assertEqual(bindtest[0].original, sunlight)
        
        lightnode.light = self.yoursunlight
        lightnode.save()
        
        loadedlightnode = collada.scene.LightNode.load(self.dummy, fromstring(tostring(lightnode.xmlnode)))
        self.assertEqual(loadedlightnode.light.id, 'yoursunlight')
        
    def test_scene_camera_node_saving(self):
        cam = collada.camera.Camera("mycam", 45.0, 0.01, 1000.0)
        camnode = collada.scene.CameraNode(cam)
        bindtest = list(camnode.objects('camera'))
        self.assertEqual(camnode.camera, cam)
        self.assertEqual(len(bindtest), 1)
        self.assertEqual(bindtest[0].original, cam)
        
        camnode.camera = self.yourcam
        camnode.save()
        
        loadedcamnode = collada.scene.CameraNode.load(self.dummy, fromstring(tostring(camnode.xmlnode)))
        self.assertEqual(loadedcamnode.camera.id, 'yourcam')

    def test_scene_translate_node(self):
        translate = collada.scene.TranslateTransform(0.1, 0.2, 0.3)
        self.assertAlmostEqual(translate.x, 0.1)
        self.assertAlmostEqual(translate.y, 0.2)
        self.assertAlmostEqual(translate.z, 0.3)
        loaded_translate = collada.scene.TranslateTransform.load(self.dummy, fromstring(tostring(translate.xmlnode)))
        self.assertAlmostEqual(loaded_translate.x, 0.1)
        self.assertAlmostEqual(loaded_translate.y, 0.2)
        self.assertAlmostEqual(loaded_translate.z, 0.3)
        
    def test_scene_rotate_node(self):
        rotate = collada.scene.RotateTransform(0.1, 0.2, 0.3, 90)
        self.assertAlmostEqual(rotate.x, 0.1)
        self.assertAlmostEqual(rotate.y, 0.2)
        self.assertAlmostEqual(rotate.z, 0.3)
        self.assertAlmostEqual(rotate.angle, 90)
        loaded_rotate = collada.scene.RotateTransform.load(self.dummy, fromstring(tostring(rotate.xmlnode)))
        self.assertAlmostEqual(loaded_rotate.x, 0.1)
        self.assertAlmostEqual(loaded_rotate.y, 0.2)
        self.assertAlmostEqual(loaded_rotate.z, 0.3)
        self.assertAlmostEqual(loaded_rotate.angle, 90)
        
    def test_scene_scale_node(self):
        scale = collada.scene.ScaleTransform(0.1, 0.2, 0.3)
        self.assertAlmostEqual(scale.x, 0.1)
        self.assertAlmostEqual(scale.y, 0.2)
        self.assertAlmostEqual(scale.z, 0.3)
        loaded_scale = collada.scene.ScaleTransform.load(self.dummy, fromstring(tostring(scale.xmlnode)))
        self.assertAlmostEqual(loaded_scale.x, 0.1)
        self.assertAlmostEqual(loaded_scale.y, 0.2)
        self.assertAlmostEqual(loaded_scale.z, 0.3)
        
    def test_scene_matrix_node(self):
        matrix = collada.scene.MatrixTransform(numpy.array([1.0,0,0,2, 0,1,0,3, 0,0,1,4, 0,0,0,1]))
        self.assertAlmostEqual(matrix.matrix[0][0], 1.0)
        loaded_matrix = collada.scene.MatrixTransform.load(self.dummy, fromstring(tostring(matrix.xmlnode)))
        self.assertAlmostEqual(loaded_matrix.matrix[0][0], 1.0)
        
    def test_scene_lookat_node(self):
        eye = numpy.array([2.0,0,3])
        interest = numpy.array([0.0,0,0])
        upvector = numpy.array([0.0,1,0])
        lookat = collada.scene.LookAtTransform(eye, interest, upvector)
        self.assertListEqual(list(lookat.eye), list(eye))
        self.assertListEqual(list(lookat.interest), list(interest))
        self.assertListEqual(list(lookat.upvector), list(upvector))
        loaded_lookat = collada.scene.LookAtTransform.load(self.dummy, fromstring(tostring(lookat.xmlnode)))
        self.assertListEqual(list(loaded_lookat.eye), list(eye))
        self.assertListEqual(list(loaded_lookat.interest), list(interest))
        self.assertListEqual(list(loaded_lookat.upvector), list(upvector))
        
    def test_scene_node_combos(self):
        emptynode = collada.scene.Node('myemptynode')
        self.assertEqual(len(emptynode.children), 0)
        self.assertEqual(len(emptynode.transforms), 0)
        loadedempty = collada.scene.Node.load(self.dummy, fromstring(tostring(emptynode.xmlnode)))
        self.assertEqual(len(loadedempty.children), 0)
        self.assertEqual(len(loadedempty.transforms), 0)
        
        justchildren = collada.scene.Node('myjustchildrennode', children=[emptynode])
        self.assertEqual(len(justchildren.children), 1)
        self.assertEqual(len(justchildren.transforms), 0)
        self.assertEqual(justchildren.children[0], emptynode)
        loadedjustchildren = collada.scene.Node.load(self.dummy, fromstring(tostring(justchildren.xmlnode)))
        self.assertEqual(len(loadedjustchildren.children), 1)
        self.assertEqual(len(loadedjustchildren.transforms), 0)
        
        scale = collada.scene.ScaleTransform(0.1, 0.2, 0.3)
        justtransform = collada.scene.Node('myjusttransformnode', transforms=[scale])
        self.assertEqual(len(justtransform.children), 0)
        self.assertEqual(len(justtransform.transforms), 1)
        self.assertEqual(justtransform.transforms[0], scale)
        loadedjusttransform = collada.scene.Node.load(self.dummy, fromstring(tostring(justtransform.xmlnode)))
        self.assertEqual(len(loadedjusttransform.children), 0)
        self.assertEqual(len(loadedjusttransform.transforms), 1)
        
        both = collada.scene.Node('mybothnode', children=[justchildren, justtransform], transforms=[scale])
        self.assertEqual(len(both.children), 2)
        self.assertEqual(len(both.transforms), 1)
        self.assertEqual(both.transforms[0], scale)
        self.assertEqual(both.children[0], justchildren)
        self.assertEqual(both.children[1], justtransform)
        loadedboth = collada.scene.Node.load(self.dummy, fromstring(tostring(both.xmlnode)))
        self.assertEqual(len(both.children), 2)
        self.assertEqual(len(both.transforms), 1)
        
    def test_scene_node_saving(self):
        myemptynode = collada.scene.Node('myemptynode')
        rotate = collada.scene.RotateTransform(0.1, 0.2, 0.3, 90)
        scale = collada.scene.ScaleTransform(0.1, 0.2, 0.3)
        mynode = collada.scene.Node('mynode', children=[myemptynode], transforms=[rotate, scale])
        self.assertEqual(mynode.id, 'mynode')
        self.assertEqual(mynode.children[0], myemptynode)
        self.assertEqual(mynode.transforms[0], rotate)
        self.assertEqual(mynode.transforms[1], scale)
        
        translate = collada.scene.TranslateTransform(0.1, 0.2, 0.3)
        mynode.transforms.append(translate)
        mynode.transforms.pop(0)
        youremptynode = collada.scene.Node('youremptynode')
        mynode.children.append(youremptynode)
        mynode.id = 'yournode'
        mynode.save()

        yournode = collada.scene.Node.load(self.dummy, fromstring(tostring(mynode.xmlnode)))
        self.assertEqual(yournode.id, 'yournode')
        self.assertEqual(len(yournode.children), 2)
        self.assertEqual(len(yournode.transforms), 2)
        self.assertEqual(yournode.children[0].id, 'myemptynode')
        self.assertEqual(yournode.children[1].id, 'youremptynode')
        self.assertTrue(type(yournode.transforms[0]) is collada.scene.ScaleTransform)
        self.assertTrue(type(yournode.transforms[1]) is collada.scene.TranslateTransform)

if __name__ == '__main__':
    unittest2.main()
