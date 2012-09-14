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
        self.dummy = collada.Collada(validate_output=True)
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath( __file__ )), "data")        
    def test_mug1(self):

        obj = collada.Collada(os.path.join(self.data_dir,'mug1.dae'),version='1.5.0')
        assert(len(obj.articulated_systems)==2)
        return obj

    def test_robot(self):
        obj = collada.Collada(os.path.join(self.data_dir, 'barrett-wamhand.dae'),version='1.5.0')
        assert(len(obj.articulated_systems)==2)
        assert(len(obj.geometries)==18)
        assert(len(obj.kinematics_models[0].joints)==16)
        assert(len(obj.kinematics_models[0].links)==1)
        assert(len(obj.kinematics_scenes[0].instance_articulated_systems)==1)
        return obj

    def test_scene(self):
        obj = collada.Collada(os.path.join(self.data_dir, 'lab3external.dae'),version='1.5.0')
        assert(len(obj.kinematics_scenes)==1)
        assert(len(obj.ikscene.kscene.instance_articulated_systems)==13)
        return obj

if __name__ == '__main__':
    unittest.main()
