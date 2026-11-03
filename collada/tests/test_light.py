import io

import pytest
import collada
from collada.common import E, tag
import unittest
from collada.xmlutil import etree

fromstring = etree.fromstring
tostring = etree.tostring


class TestLight(unittest.TestCase):

    def setUp(self):
        self.dummy = collada.Collada(validate_output=True)

    def test_directional_light_saving(self):
        dirlight = collada.light.DirectionalLight("mydirlight", (1, 1, 1))
        self.assertEqual(dirlight.id, "mydirlight")
        self.assertTupleEqual(dirlight.color, (1, 1, 1))
        self.assertTupleEqual(tuple(dirlight.direction), (0, 0, -1))
        self.assertIsNotNone(str(dirlight))
        dirlight.color = (0.1, 0.2, 0.3)
        dirlight.id = "yourdirlight"
        dirlight.save()
        loaded_dirlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(dirlight.xmlnode)))
        self.assertTrue(isinstance(loaded_dirlight, collada.light.DirectionalLight))
        self.assertTupleEqual(loaded_dirlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(loaded_dirlight.id, "yourdirlight")

    def test_ambient_light_saving(self):
        ambientlight = collada.light.AmbientLight("myambientlight", (1, 1, 1))
        self.assertEqual(ambientlight.id, "myambientlight")
        self.assertTupleEqual(ambientlight.color, (1, 1, 1))
        self.assertIsNotNone(str(ambientlight))
        ambientlight.color = (0.1, 0.2, 0.3)
        ambientlight.id = "yourambientlight"
        ambientlight.save()
        loaded_ambientlight = collada.light.Light.load(self.dummy, {}, fromstring(tostring(ambientlight.xmlnode)))
        self.assertTrue(isinstance(loaded_ambientlight, collada.light.AmbientLight))
        self.assertTupleEqual(ambientlight.color, (0.1, 0.2, 0.3))
        self.assertEqual(ambientlight.id, "yourambientlight")

    def test_point_light_saving(self):
        pointlight = collada.light.PointLight("mypointlight", (1, 1, 1))
        self.assertEqual(pointlight.id, "mypointlight")
        self.assertTupleEqual(pointlight.color, (1, 1, 1))
        self.assertEqual(pointlight.quad_att, None)
        self.assertEqual(pointlight.constant_att, None)
        self.assertEqual(pointlight.linear_att, None)
        self.assertEqual(pointlight.zfar, None)
        self.assertIsNotNone(str(pointlight))

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
        spotlight = collada.light.SpotLight("myspotlight", (1, 1, 1))
        self.assertEqual(spotlight.id, "myspotlight")
        self.assertTupleEqual(spotlight.color, (1, 1, 1))
        self.assertEqual(spotlight.constant_att, None)
        self.assertEqual(spotlight.linear_att, None)
        self.assertEqual(spotlight.quad_att, None)
        self.assertEqual(spotlight.falloff_ang, None)
        self.assertEqual(spotlight.falloff_exp, None)
        self.assertIsNotNone(str(spotlight))

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
    unittest.main()


@pytest.mark.parametrize('kind,field,value', [
    ('point', 'constant_att', 1), ('point', 'linear_att', 0.2),
    ('spot', 'constant_att', 1), ('spot', 'linear_att', 0.2),
    ('spot', 'quad_att', 0.3), ('spot', 'falloff_ang', 30),
])
def test_adding_earlier_light_parameters_keeps_schema_order(kind, field, value):
    mesh = collada.Collada(validate_output=True)
    if kind == 'point':
        light = collada.light.PointLight('light', (1, 1, 1), quad_att=0.5)
    else:
        light = collada.light.SpotLight('light', (1, 1, 1), falloff_exp=4)
    mesh.lights.append(light)
    mesh.scene = collada.scene.Scene('scene', [collada.scene.Node('node', [collada.scene.LightNode(light)])])
    mesh.scenes.append(mesh.scene)
    light.xmlnode.append(E.extra(E.technique(E.note('keep'), profile='TEST')))
    setattr(light, field, value)
    for _ in range(2):
        output = io.BytesIO()
        mesh.write(output)
        mesh = collada.Collada(io.BytesIO(output.getvalue()), validate_output=True)
        light = next(mesh.scene.objects('light')).original
        assert getattr(light, field) == value
        assert light.xmlnode.find(f"{tag('extra')}/{tag('technique')}/{tag('note')}").text == 'keep'
        if kind == 'point':
            assert light.quad_att == 0.5
        else:
            assert light.falloff_exp == 4


@pytest.mark.parametrize('kind', ['point', 'spot'])
@pytest.mark.parametrize('operation', ['update', 'remove'])
def test_existing_light_parameter_controls(kind, operation):
    mesh = collada.Collada(validate_output=True)
    cls = collada.light.PointLight if kind == 'point' else collada.light.SpotLight
    light = cls('light', (1, 1, 1), constant_att=1, linear_att=0.2, quad_att=0.3)
    mesh.lights.append(light)
    light.linear_att = 0.4 if operation == 'update' else None
    output = io.BytesIO()
    mesh.write(output)
    loaded = collada.Collada(io.BytesIO(output.getvalue()), validate_output=True).lights[0]
    assert loaded.linear_att == light.linear_att
