import unittest2
import collada
from lxml.etree import fromstring, tostring
import StringIO

class TestMaterial(unittest2.TestCase):

    def setUp(self):
        self.dummy_collada_text = """
        <COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
        </COLLADA>
        """
        self.dummy = collada.Collada(StringIO.StringIO(self.dummy_collada_text))

    def test_effect_saving(self):
        effect = collada.material.Effect("myeffect", [], "phong",
                       emission = (0.1, 0.2, 0.3),
                       ambient = (0.4, 0.5, 0.6),
                       diffuse = (0.7, 0.8, 0.9),
                       specular = (0.3, 0.2, 0.1),
                       shininess = 0.4,
                       reflective = (0.7, 0.6, 0.5),
                       reflectivity = 0.8,
                       transparent = (0.2, 0.4, 0.6),
                       transparency = 0.9)
        
        self.assertEqual(effect.id, "myeffect")
        self.assertEqual(effect.shininess, 0.4)
        self.assertEqual(effect.reflectivity, 0.8)
        self.assertEqual(effect.transparency, 0.9)
        self.assertTupleEqual(effect.emission, (0.1, 0.2, 0.3))
        self.assertTupleEqual(effect.ambient, (0.4, 0.5, 0.6))
        self.assertTupleEqual(effect.diffuse, (0.7, 0.8, 0.9))
        self.assertTupleEqual(effect.specular, (0.3, 0.2, 0.1))
        self.assertTupleEqual(effect.reflective, (0.7, 0.6, 0.5))
        self.assertTupleEqual(effect.transparent, (0.2, 0.4, 0.6))
        
        effect.id = "youreffect"
        effect.shininess = 7.0
        effect.reflectivity = 2.0
        effect.transparency = 3.0
        effect.emission = (1.1, 1.2, 1.3)
        effect.ambient = (1.4, 1.5, 1.6)
        effect.diffuse = (1.7, 1.8, 1.9)
        effect.specular = (1.3, 1.2, 1.1)
        effect.reflective = (1.7, 1.6, 1.5)
        effect.transparent = (1.2, 1.4, 1.6)
        effect.save()
        
        loaded_effect = collada.material.Effect.load(self.dummy, {},
                                    fromstring(tostring(effect.xmlnode)))
        
        self.assertEqual(effect.id, "youreffect")
        self.assertEqual(effect.shininess, 7.0)
        self.assertEqual(effect.reflectivity, 2.0)
        self.assertEqual(effect.transparency, 3.0)
        self.assertTupleEqual(effect.emission, (1.1, 1.2, 1.3))
        self.assertTupleEqual(effect.ambient, (1.4, 1.5, 1.6))
        self.assertTupleEqual(effect.diffuse, (1.7, 1.8, 1.9))
        self.assertTupleEqual(effect.specular, (1.3, 1.2, 1.1))
        self.assertTupleEqual(effect.reflective, (1.7, 1.6, 1.5))
        self.assertTupleEqual(effect.transparent, (1.2, 1.4, 1.6))
        
    #def cimage
    #def sampler2d
    #def surface
    #def map

if __name__ == '__main__':
    unittest2.main()
