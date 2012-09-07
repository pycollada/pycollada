"""Tests 1.5 kinematics spec
"""
import os
import collada
def test_collada():
    obj = collada.Collada('data/mug1.dae',version='1.5.0')

if __name__=='__main__':
    test_collada()
    
