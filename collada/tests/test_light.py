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

    def test_directional_light_saving(self):
        dirlight = collada.light.DirectionalLight("mydirlight", (1,1,1))
        self.assertEqual(dirlight.id, "mydirlight")
        self.assertTupleEqual(dirlight.color, (1,1,1))
        self.assertTupleEqual(tuple(dirlight.direction), (0,0,-1))
        dirlight.color = (0.1, 0.2, 0.3)
        dirlight.id = "yourdirlight"
        dirlight.save()
        loaded_dirlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(dirlight.xmlnode)))
        self.assertTrue(isinstance(loaded_dirlight, collada.light.DirectionalLight))
        self.assertTupleEqual(loaded_dirlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(loaded_dirlight.id, "yourdirlight")
        
    def test_ambient_light_saving(self):
        ambientlight = collada.light.AmbientLight("myambientlight", (1,1,1))
        self.assertEqual(ambientlight.id, "myambientlight")
        self.assertTupleEqual(ambientlight.color, (1,1,1))
        ambientlight.color = (0.1, 0.2, 0.3)
        ambientlight.id = "yourambientlight"
        ambientlight.save()
        loaded_ambientlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(ambientlight.xmlnode)))
        self.assertTrue(isinstance(loaded_ambientlight, collada.light.AmbientLight))
        self.assertTupleEqual(ambientlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(ambientlight.id, "yourambientlight")
        
    def test_point_light_saving(self):
        pointlight = collada.light.PointLight("mypointlight", (1,1,1), 0.4)
        self.assertEqual(pointlight.id, "mypointlight")
        self.assertTupleEqual(pointlight.color, (1,1,1))
        self.assertEqual(pointlight.quad_att, 0.4)
        self.assertEqual(pointlight.constant_att, None)
        self.assertEqual(pointlight.linear_att, None)
        self.assertEqual(pointlight.zfar, None)

        pointlight.color = (0.1, 0.2, 0.3)
        pointlight.constant_att = 0.7
        pointlight.linear_att = 0.8
        pointlight.quad_att = 0.9
        pointlight.id = "yourpointlight"
        pointlight.save()
        loaded_pointlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(pointlight.xmlnode)))
        self.assertTrue(isinstance(loaded_pointlight, collada.light.PointLight))
        self.assertTupleEqual(loaded_pointlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(loaded_pointlight.constant_att, 0.7)
        self.assertEqual(loaded_pointlight.linear_att, 0.8)
        self.assertEqual(loaded_pointlight.quad_att, 0.9)
        self.assertEqual(loaded_pointlight.zfar, None)
        self.assertEqual(loaded_pointlight.id, "yourpointlight")
        
        loaded_pointlight.zfar = 0.2
        loaded_pointlight.save()
        loaded_pointlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(loaded_pointlight.xmlnode)))
        self.assertEqual(loaded_pointlight.zfar, 0.2)
        
    def test_spot_light_saving(self):
        spotlight = collada.light.SpotLight("myspotlight", (1,1,1))
        self.assertEqual(spotlight.id, "myspotlight")
        self.assertTupleEqual(spotlight.color, (1,1,1))
        self.assertEqual(spotlight.constant_att, None)
        self.assertEqual(spotlight.linear_att, None)
        self.assertEqual(spotlight.quad_att, None)
        self.assertEqual(spotlight.falloff_ang, None)
        self.assertEqual(spotlight.falloff_exp, None)

        spotlight.color = (0.1, 0.2, 0.3)
        spotlight.constant_att = 0.7
        spotlight.linear_att = 0.8
        spotlight.quad_att = 0.9
        spotlight.id = "yourspotlight"
        spotlight.save()
        loaded_spotlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(spotlight.xmlnode)))
        self.assertTrue(isinstance(loaded_spotlight, collada.light.SpotLight))
        self.assertTupleEqual(loaded_spotlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(loaded_spotlight.constant_att, 0.7)
        self.assertEqual(loaded_spotlight.linear_att, 0.8)
        self.assertEqual(loaded_spotlight.quad_att, 0.9)
        self.assertEqual(loaded_spotlight.falloff_ang, None)
        self.assertEqual(loaded_spotlight.falloff_exp, None)
        self.assertEqual(loaded_spotlight.id, "yourspotlight")
        
        loaded_spotlight.falloff_ang = 180
        loaded_spotlight.falloff_exp = 2
        loaded_spotlight.save()
        loaded_spotlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(loaded_spotlight.xmlnode)))
        self.assertEqual(loaded_spotlight.falloff_ang, 180)
        self.assertEqual(loaded_spotlight.falloff_exp, 2)
        

if __name__ == '__main__':
    unittest2.main()
