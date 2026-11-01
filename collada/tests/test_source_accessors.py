"""Accessor layouts must survive public scene loading and save/reload."""

import io
from pathlib import Path

import numpy
import pytest

import collada
from collada.common import DaeMalformedError, DaeUnsupportedError
from collada.xmlutil import etree


def load_source(values, params, **attributes):
    attributes.setdefault('count', '2')
    attrs = ' '.join('%s="%s"' % item for item in attributes.items())
    xml = ('<source xmlns="http://www.collada.org/2005/11/COLLADASchema" id="values">'
           '<float_array id="array" count="%s">%s</float_array>'
           '<technique_common><accessor source="#array" %s>%s</accessor>'
           '</technique_common></source>') % (len(values), ' '.join(map(str, values)), attrs, params)
    return collada.source.Source.load(collada.Collada(), {}, etree.fromstring(xml))


XYZ = ''.join('<param name="%s" type="float"/>' % c for c in ('X', 'Y', 'Z'))


@pytest.mark.parametrize('values,attributes', [
    ([99, 0, 1, 2, 3, 4, 5], {'offset': '1', 'stride': '3'}),
    ([0, 1, 2, 99, 3, 4, 5, 99], {'stride': '4'}),
    ([0, 1, 2, 3, 4, 5, 99, 99, 99], {'stride': '3'}),
    ([0, 1, 2, 99, 3, 4, 5], {'stride': '4'}),
    ([0, 1, 2, 3, 4, 5], {'stride': '3'}),
])
def test_float_source_layout(values, attributes):
    source = load_source(values, XYZ, **attributes)
    numpy.testing.assert_array_equal(source.data, [[0, 1, 2], [3, 4, 5]])
    assert source.components == ('X', 'Y', 'Z')
    source.save()
    reloaded = collada.source.Source.load(collada.Collada(), {}, etree.fromstring(etree.tostring(source.xmlnode)))
    numpy.testing.assert_array_equal(reloaded.data, source.data)
    assert reloaded.components == source.components


@pytest.mark.parametrize('unnamed', [0, 1, 2, 3])
def test_unnamed_float_parameters(unnamed):
    nodes = ['<param name="%s" type="float"/>' % c for c in ('X', 'Y', 'Z')]
    nodes.insert(unnamed, '<param type="float"/>')
    params = ''.join(nodes)
    values = []
    for row in ([0, 1, 2], [3, 4, 5]):
        row.insert(unnamed, 99)
        values.extend(row)
    source = load_source(values, params, stride='4')
    numpy.testing.assert_array_equal(source.data, [[0, 1, 2], [3, 4, 5]])
    assert source.components == ('X', 'Y', 'Z')


@pytest.mark.parametrize('params,values,expected', [
    ('<param name="U" type="float"/><param name="V" type="float"/>',
     [99, 0, 1, 88, 2, 3, 88], [[0, 1], [2, 3]]),
    ('<param name="S" type="float"/><param name="T" type="float"/><param name="P" type="float"/>',
     [99, 0, 1, 9, 88, 2, 3, 9, 88], [[0, 1], [2, 3]]),
])
def test_texture_accessors(params, values, expected):
    source = load_source(values, params, offset='1', stride=str((len(values) - 1) // 2))
    assert source.components == ('S', 'T')
    numpy.testing.assert_array_equal(source.data, expected)


def test_default_stride_and_offset():
    source = load_source([1, 2, 99], '<param name="WEIGHT" type="float"/>')
    numpy.testing.assert_array_equal(source.data, [[1], [2]])


@pytest.mark.parametrize('count,stride', [('0', '0'), ('0', '3')])
def test_empty_accessor(count, stride):
    source = load_source([], XYZ, count=count, stride=stride)
    assert source.data.shape == (0, 3)


@pytest.mark.parametrize('offset', [0, 1])
def test_matrix_source_compatibility(offset):
    # Skin controllers already reshape this source to (-1, 4, 4).
    values = [99] * offset + list(range(32))
    source = load_source(values, '<param name="TRANSFORM" type="float4x4"/>',
                         offset=str(offset), stride='16')
    numpy.testing.assert_array_equal(source.data.reshape(2, 4, 4), numpy.arange(32).reshape(2, 4, 4))
    assert source.components == ('TRANSFORM',)


@pytest.mark.parametrize('attributes', [
    {'count': '-1', 'stride': '3'},
    {'count': 'bad', 'stride': '3'},
    {'offset': '-1', 'stride': '3'},
    {'offset': 'bad', 'stride': '3'},
    {'stride': '0'},
    {'stride': '2'},
    {'stride': 'bad'},
    {'count': '3', 'stride': '3'},
])
def test_invalid_accessor_is_a_dae_error(attributes):
    with pytest.raises(DaeMalformedError):
        load_source(list(range(6)), XYZ, **attributes)


def test_no_output_parameters():
    with pytest.raises(DaeUnsupportedError):
        load_source([1, 2], '<param type="float"/>')


def test_full_scene_accessor_round_trip():
    path = Path(__file__).with_name('data') / 'source_accessors.dae'
    mesh = collada.Collada(str(path), validate_output=True)
    if mesh.validator is not None:
        assert mesh.validator.validate(etree.parse(str(path)))
    expected = numpy.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    numpy.testing.assert_array_equal(mesh.geometries[0].primitives[0].vertex, expected)
    bound = next(mesh.scene.objects('geometry'))
    numpy.testing.assert_array_equal(next(bound.primitives()).vertex, expected + [2, 3, 4])
    # Exercise editing as well as loading and serializing the projected source.
    mesh.geometries[0].sourceById['positions'].data[1, 0] = 2
    expected[1, 0] = 2
    output = io.BytesIO()
    mesh.write(output)
    reloaded = collada.Collada(io.BytesIO(output.getvalue()), validate_output=True)
    numpy.testing.assert_array_equal(reloaded.geometries[0].primitives[0].vertex, expected)
    bound = next(reloaded.scene.objects('geometry'))
    numpy.testing.assert_array_equal(next(bound.primitives()).vertex, expected + [2, 3, 4])


@pytest.mark.parametrize('param_type,size', [
    ('float', 1), ('float2', 2), ('float3', 3), ('float4', 4),
    ('float2x2', 4), ('float3x3', 9), ('float4x4', 16),
])
def test_float_type_size_lookup(param_type, size):
    assert collada.source.get_float_type_size(param_type) == size


@pytest.mark.parametrize('param_type', ['int', 'double', 'float1', 'float2x3', 'float5', '', 'FLOAT'])
def test_float_type_size_rejects_unsupported_types(param_type):
    with pytest.raises(collada.common.DaeUnsupportedError):
        collada.source.get_float_type_size(param_type)
