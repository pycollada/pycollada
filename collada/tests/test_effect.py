import unittest2
import collada
from lxml import etree as ElementTree

class TestMaterialEffect(unittest2.TestCase):

    def setUp(self):
        self.effect = collada.material.Effect("testeffect", [], "phong",
                       emission = (0.0, 0.0, 0.0),
                       ambient = (0.0, 0.0, 0.0),
                       diffuse = (0.0, 0.0, 0.0),
                       specular = (0.0, 0.0, 0.0),
                       shininess = 0.0,
                       reflective = (0.0, 0.0, 0.0),
                       reflectivity = 0.0,
                       transparent = (0.0, 0.0, 0.0),
                       transparency = 0.0)

    def test_effect_saving(self):
        self.assertEqual(self.effect.id, "testeffect")
        self.effect.shininess = 7.0
        self.effect.save()
        #print ElementTree.tostring(self.effect.xmlnode)

if __name__ == '__main__':
    unittest2.main()
