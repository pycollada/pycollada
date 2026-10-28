from io import BytesIO

import numpy
import pytest

import collada


KINDS = ['triangles', 'polylist', 'polygons', 'lines']


def make_primitive(kind, normal=(1., 1., 1.)):
    document = collada.Collada(validate_output=True)
    vertices = collada.source.FloatSource(
        'vertices', numpy.array([[0., 0., 0.], [1., 0., -1.], [0., 1., -1.]]), ('X', 'Y', 'Z'))
    sources = [vertices]
    inputs = collada.source.InputList()
    inputs.addInput(0, 'VERTEX', '#vertices')
    indices = numpy.array([0, 1, 1, 2] if kind == 'lines' else [0, 1, 2])
    if normal is not None:
        sources.append(collada.source.FloatSource('normals', numpy.array([normal]) / numpy.sqrt(3), ('X', 'Y', 'Z')))
        inputs.addInput(1, 'NORMAL', '#normals')
        indices = numpy.column_stack((indices, numpy.zeros(len(indices), dtype=int))).ravel()
    geometry = collada.geometry.Geometry(document, 'geometry', 'geometry', sources)
    if kind == 'triangles':
        primitive = geometry.createTriangleSet(indices, inputs)
    elif kind == 'polylist':
        primitive = geometry.createPolylist(indices, numpy.array([3]), inputs)
    elif kind == 'polygons':
        primitive = geometry.createPolygons([indices], inputs)
    else:
        primitive = geometry.createLineSet(indices, inputs)
    return document, geometry, primitive


def transform(linear, translation=(5., -6., 7.)):
    matrix = numpy.identity(4)
    matrix[:3, :3] = linear
    matrix[:3, 3] = translation
    return matrix


ROTATION = numpy.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
CASES = [
    (transform(numpy.identity(3), (0., 0., 0.)), (1., 1., 1.)),
    (transform(numpy.identity(3)), (1., 1., 1.)),
    (transform(ROTATION), (-1., 1., 1.)),
    (transform(numpy.diag([2., 3., 4.])), (0.5, 1. / 3, 0.25)),
    (transform(numpy.diag([2., 2., 2.])), (0.5, 0.5, 0.5)),
    (transform([[1., 2., 0.], [0., 1., 0.], [0., 0., 1.]]), (1., -1., 1.)),
    (transform(ROTATION.dot(numpy.diag([2., 3., 4.]))), (-1. / 3, 0.5, 0.25)),
    (transform(numpy.diag([-2., 3., 4.])), (-0.5, 1. / 3, 0.25)),
]


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('matrix,expected', CASES,
                         ids=['identity', 'translation', 'rotation', 'scale', 'uniform', 'shear', 'combined', 'reflection'])
def test_bound_normals(kind, matrix, expected):
    _, _, primitive = make_primitive(kind)
    original = primitive.normal.copy()
    bound = primitive.bind(matrix, {})
    numpy.testing.assert_allclose(bound.normal, [numpy.array(expected) / numpy.sqrt(3)], atol=1e-7)
    numpy.testing.assert_array_equal(bound.normal_index, primitive.normal_index)
    numpy.testing.assert_array_equal(primitive.normal, original)
    for edge in (bound.vertex[1] - bound.vertex[0], bound.vertex[2] - bound.vertex[0]):
        numpy.testing.assert_allclose(bound.normal.dot(edge), 0., atol=1e-7)


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('linear,expected', [
    (numpy.diag([2., 3., 0.]), [0., 0., 6.]),
    (numpy.diag([2., 0., 0.]), [0., 0., 0.]),
    ([[2., 0., 0.], [0., 3., 0.], [1., 0., 0.]], [-3., 0., 6.]),
])
def test_collapsed_transforms(kind, linear, expected):
    _, _, primitive = make_primitive(kind)
    bound = primitive.bind(transform(linear), {})
    assert numpy.isfinite(bound.normal).all()
    numpy.testing.assert_allclose(bound.normal, [numpy.array(expected) / numpy.sqrt(3)], atol=1e-7)
    for edge in (bound.vertex[1] - bound.vertex[0], bound.vertex[2] - bound.vertex[0]):
        numpy.testing.assert_allclose(bound.normal.dot(edge), 0., atol=1e-7)


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('normal', [None, (0., 0., 0.)])
def test_missing_and_zero_normals(kind, normal):
    _, _, primitive = make_primitive(kind, normal)
    bound = primitive.bind(transform(numpy.diag([2., 3., 0.])), {})
    if normal is None:
        assert bound.normal is None
    else:
        numpy.testing.assert_array_equal(bound.normal, [[0., 0., 0.]])


def test_scene_save_reload():
    document, geometry, primitive = make_primitive('triangles')
    geometry.primitives.append(primitive)
    document.geometries.append(geometry)
    matrix = transform(ROTATION.dot(numpy.diag([2., 3., 4.])))
    node = collada.scene.Node('object', children=[collada.scene.GeometryNode(geometry)],
                              transforms=[collada.scene.MatrixTransform(matrix.ravel())])
    document.scene = collada.scene.Scene('scene', [node])
    document.scenes.append(document.scene)
    stream = BytesIO()
    document.write(stream)
    loaded = collada.Collada(BytesIO(stream.getvalue()))
    bound = next(next(loaded.scene.objects('geometry')).primitives())
    numpy.testing.assert_allclose(bound.normal, [numpy.array([-1. / 3, 0.5, 0.25]) / numpy.sqrt(3)], atol=1e-6)
