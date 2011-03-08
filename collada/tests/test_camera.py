import unittest2
import collada
import StringIO
from lxml.etree import fromstring, tostring

class TestCamera(unittest2.TestCase):

    def setUp(self):
        self.dummy_collada_text = """
        <COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
        </COLLADA>
        """
        self.dummy = collada.Collada(StringIO.StringIO(self.dummy_collada_text))

    def test_camera_saving(self):
        camera = collada.camera.Camera("mycam", 45.0, 0.01, 1000.0)
        self.assertEqual(camera.id, "mycam")
        self.assertEqual(camera.fov, 45.0)
        self.assertEqual(camera.near, 0.01)
        self.assertEqual(camera.far, 1000.0)
        camera.fov = 90.0
        camera.save()
        loaded_camera = collada.camera.Camera.load(self.dummy, {}, fromstring(tostring(camera.xmlnode)))
        self.assertEqual(loaded_camera.fov, 90.0)

if __name__ == '__main__':
    unittest2.main()
