import unittest2
import collada
from lxml.etree import fromstring, tostring

class TestCamera(unittest2.TestCase):

    def setUp(self):
        self.dummy = collada.Collada()

    def test_perspective_camera_xfov_yfov_aspect_ratio(self):
        #test invalid xfov,yfov,aspect_ratio combinations
        with self.assertRaises(collada.DaeMalformedError):
            cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=None, yfov=None, aspect_ratio=None)
        with self.assertRaises(collada.DaeMalformedError):
            cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=0.2, yfov=30, aspect_ratio=50)
        with self.assertRaises(collada.DaeMalformedError):
            cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=None, yfov=None, aspect_ratio=50)
            
        #xfov alone
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=30, yfov=None, aspect_ratio=None)
        self.assertEqual(cam.xfov, 30)
        self.assertIsNone(cam.yfov)
        self.assertIsNone(cam.aspect_ratio)
        
        #yfov alone
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=None, yfov=50, aspect_ratio=None)
        self.assertIsNone(cam.xfov)
        self.assertEqual(cam.yfov, 50)
        self.assertIsNone(cam.aspect_ratio)
        
        #xfov + yfov
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=30, yfov=50, aspect_ratio=None)
        self.assertEqual(cam.xfov, 30)
        self.assertEqual(cam.yfov, 50)
        self.assertIsNone(cam.aspect_ratio)
        
        #xfov + aspect_ratio
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=30, yfov=None, aspect_ratio=1)
        self.assertEqual(cam.xfov, 30)
        self.assertIsNone(cam.yfov)
        self.assertEqual(cam.aspect_ratio, 1)
        
        #yfov + aspect_ratio
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=None, yfov=50, aspect_ratio=1)
        self.assertIsNone(cam.xfov)
        self.assertEqual(cam.yfov, 50)
        self.assertEqual(cam.aspect_ratio, 1)
        
    def test_perspective_camera_saving(self):
        cam = collada.camera.PerspectiveCamera("mycam", 1, 1000, xfov=30)
        
        self.assertEqual(cam.id, "mycam")
        self.assertEqual(cam.znear, 1)
        self.assertEqual(cam.zfar, 1000)
        self.assertEqual(cam.xfov, 30)
        self.assertEqual(cam.yfov, None)
        self.assertEqual(cam.aspect_ratio, None)
        
        cam.save()
        self.assertEqual(cam.id, "mycam")
        self.assertEqual(cam.znear, 1)
        self.assertEqual(cam.zfar, 1000)
        self.assertEqual(cam.xfov, 30)
        self.assertEqual(cam.yfov, None)
        self.assertEqual(cam.aspect_ratio, None)
        
        cam = collada.camera.PerspectiveCamera.load(self.dummy, {}, fromstring(tostring(cam.xmlnode)))
        self.assertEqual(cam.id, "mycam")
        self.assertEqual(cam.znear, 1)
        self.assertEqual(cam.zfar, 1000)
        self.assertEqual(cam.xfov, 30)
        self.assertEqual(cam.yfov, None)
        self.assertEqual(cam.aspect_ratio, None)
        
        cam.id = "yourcam"
        cam.znear = 5
        cam.zfar = 500
        cam.xfov = None
        cam.yfov = 50
        cam.aspect_ratio = 1.3
        cam.save()
        cam = collada.camera.PerspectiveCamera.load(self.dummy, {}, fromstring(tostring(cam.xmlnode)))
        self.assertEqual(cam.id, "yourcam")
        self.assertEqual(cam.znear, 5)
        self.assertEqual(cam.zfar, 500)
        self.assertEqual(cam.xfov, None)
        self.assertEqual(cam.yfov, 50)
        self.assertEqual(cam.aspect_ratio, 1.3)
        
        cam.xfov = 20
        with self.assertRaises(collada.DaeMalformedError):
            cam.save()

if __name__ == '__main__':
    unittest2.main()
