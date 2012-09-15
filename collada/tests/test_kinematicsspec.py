"""Tests 1.5 kinematics spec
"""
import os
import collada
from collada.util import unittest
from collada.xmlutil import etree

fromstring = etree.fromstring
tostring = etree.tostring

class TestKinematicsScene(unittest.TestCase):
    def setUp(self):
        collada.set_collada_version(collada.VERSION_1_5)
        self.dummy = collada.Collada(validate_output=True)
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath( __file__ )), "data")
    
    def tearDown(self):
        collada.set_collada_version(collada.DEFAULT_VERSION)
    
    def test_mug1(self):

        obj = collada.Collada(os.path.join(self.data_dir,'mug1.dae'))
        assert(len(obj.articulated_systems)==2)
        return obj

    def test_robot(self):
        obj = collada.Collada(os.path.join(self.data_dir, 'barrett-wamhand.dae'))
        assert(len(obj.articulated_systems)==2)
        assert(len(obj.geometries)==18)
        assert(len(obj.kinematics_models[0].joints)==16)
        assert(len(obj.kinematics_models[0].links)==1)
        assert(len(obj.kinematics_scenes[0].instance_articulated_systems)==1)
        return obj

    def test_scene(self):
        obj = collada.Collada(os.path.join(self.data_dir, 'lab3external.dae'))
        assert(len(obj.kinematics_scenes)==1)
        assert(len(obj.ikscene.kscene.instance_articulated_systems)==13)
        return obj

if __name__ == '__main__':
    unittest.main()
