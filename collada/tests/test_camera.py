import unittest2
import collada
from lxml.etree import fromstring, tostring

class TestCamera(unittest2.TestCase):

    def setUp(self):
        self.dummy = collada.Collada()

    def test_camera_saving(self):
        camera = collada.camera.Camera("mycam", 45.0, 0.01, 1000.0)
        self.assertEqual(camera.id, "mycam")
        self.assertEqual(camera.fov, 45.0)
        self.assertEqual(camera.near, 0.01)
        self.assertEqual(camera.far, 1000.0)
        self.assertIsNotNone(str(camera))
        camera.fov = 90.0
        camera.near = 0.02
        camera.far = 500.2
        camera.id = "yourcam"
        camera.save()
        loaded_camera = collada.camera.Camera.load(self.dummy, {}, fromstring(tostring(camera.xmlnode)))
        self.assertEqual(loaded_camera.fov, 90.0)
        self.assertEqual(loaded_camera.near, 0.02)
        self.assertEqual(loaded_camera.far, 500.2)
        self.assertEqual(camera.id, "yourcam")

if __name__ == '__main__':
    unittest2.main()
