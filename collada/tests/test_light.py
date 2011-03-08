import unittest2
import collada
import StringIO
from lxml.etree import fromstring, tostring

class TestLight(unittest2.TestCase):

    def setUp(self):
        self.dummy_collada_text = """
        <COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
        </COLLADA>
        """
        self.dummy = collada.Collada(StringIO.StringIO(self.dummy_collada_text))

    def test_sun_light_saving(self):
        sunlight = collada.light.SunLight("mysunlight", (1,1,1))
        self.assertEqual(sunlight.id, "mysunlight")
        self.assertTupleEqual(sunlight.color, (1,1,1))
        sunlight.color = (0.1, 0.2, 0.3)
        sunlight.save()
        loaded_sunlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(sunlight.xmlnode)))
        self.assertTrue(isinstance(loaded_sunlight, collada.light.SunLight))
        self.assertTupleEqual(sunlight.color, (0.1, 0.2, 0.3))
        
    def test_ambient_light_saving(self):
        ambientlight = collada.light.AmbientLight("myambientlight", (1,1,1))
        self.assertEqual(ambientlight.id, "myambientlight")
        self.assertTupleEqual(ambientlight.color, (1,1,1))
        ambientlight.color = (0.1, 0.2, 0.3)
        ambientlight.save()
        loaded_ambientlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(ambientlight.xmlnode)))
        self.assertTrue(isinstance(loaded_ambientlight, collada.light.AmbientLight))
        self.assertTupleEqual(ambientlight.color, (0.1, 0.2, 0.3))
        
    def test_point_light_saving(self):
        pointlight = collada.light.PointLight("mypointlight", (1,1,1), 0.4, 0.5, 0.6)
        self.assertEqual(pointlight.id, "mypointlight")
        self.assertTupleEqual(pointlight.color, (1,1,1))
        self.assertEqual(pointlight.constant_att, 0.4)
        self.assertEqual(pointlight.linear_att, 0.5)
        self.assertEqual(pointlight.quad_att, 0.6)
        pointlight.color = (0.1, 0.2, 0.3)
        pointlight.constant_att = 0.7
        pointlight.linear_att = 0.8
        pointlight.quad_att = 0.9
        pointlight.save()
        loaded_pointlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(pointlight.xmlnode)))
        self.assertTrue(isinstance(loaded_pointlight, collada.light.PointLight))
        self.assertTupleEqual(pointlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(pointlight.constant_att, 0.7)
        self.assertEqual(pointlight.linear_att, 0.8)
        self.assertEqual(pointlight.quad_att, 0.9)

if __name__ == '__main__':
    unittest2.main()
