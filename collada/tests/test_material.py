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
        effect = collada.material.Effect("testeffect", [], "phong",
                       emission = (0.0, 0.0, 0.0),
                       ambient = (0.0, 0.0, 0.0),
                       diffuse = (0.0, 0.0, 0.0),
                       specular = (0.0, 0.0, 0.0),
                       shininess = 0.0,
                       reflective = (0.0, 0.0, 0.0),
                       reflectivity = 0.0,
                       transparent = (0.0, 0.0, 0.0),
                       transparency = 0.0)
        self.assertEqual(effect.id, "testeffect")
        effect.shininess = 7.0
        effect.save()
        loaded_effect = collada.material.Effect.load(self.dummy, {},
                                    fromstring(tostring(effect.xmlnode)))
        self.assertEqual(loaded_effect.shininess, 7.0)
        
    #def cimage
    #def sampler2d
    #def surface
    #def map

if __name__ == '__main__':
    unittest2.main()
