"""Tests 1.5 kinematics spec
"""
import os
import collada
def test_mug1():
    obj = collada.Collada('data/mug1.dae',version='1.5.0')
    assert(len(obj.articulated_systems)==2)
    return obj

def test_robot():
    obj = collada.Collada('data/barrett-wamhand.dae',version='1.5.0')
    assert(len(obj.articulated_systems)==2)
    assert(len(obj.geometries)==18)
    assert(len(obj.kinematics_models[0].joints)==16)
    assert(len(obj.kinematics_models[0].links)==1)
    assert(len(obj.kinematics_scenes[0].articulated_systems)==1)
    return obj

def test_scene():
    obj = collada.Collada('data/lab3external.dae',version='1.5.0')
    assert(len(obj.kinematics_scenes)==1)
    assert(len(obj.ikscene.kscene.instance_articulated_systems)==7)
    assert(len(obj.ikscene.kscene.articulated_systems)==6)
    
    return obj

if __name__=='__main__':
    obj=test_scene()
    
