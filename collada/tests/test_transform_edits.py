"""Editing transform parameters must update the saved XML and bound geometry."""
import io

import numpy as np
import pytest

import collada
from collada import scene
from collada.xmlutil import etree


KINDS = ('translate', 'rotate', 'scale', 'matrix', 'lookat')


def transform_case(kind):
    if kind == 'translate':
        return scene.TranslateTransform(0, 0, 0), {'x': 2, 'y': 3, 'z': 4}, np.array([[1, 0, 0, 2], [0, 1, 0, 3], [0, 0, 1, 4], [0, 0, 0, 1]])
    if kind == 'rotate':
        return scene.RotateTransform(1, 0, 0, 0), {'x': 0, 'y': 0, 'z': 1, 'angle': 90}, np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    if kind == 'scale':
        return scene.ScaleTransform(1, 1, 1), {'x': 2, 'y': 3, 'z': 4}, np.diag([2, 3, 4, 1])
    if kind == 'matrix':
        expected = np.array([[1, .5, 0, 2], [0, 1, 0, 3], [0, 0, 1, 4], [0, 0, 0, 1]], dtype=np.float32)
        return scene.MatrixTransform(np.identity(4).ravel()), {'matrix': expected.copy()}, expected
    expected = np.array([[0, 0, 1, 3], [1, 0, 0, 4], [0, 1, 0, 5], [0, 0, 0, 1]])
    transform = scene.LookAtTransform(np.array([0., 0., 1.]), np.zeros(3), np.array([0., 1., 0.]))
    values = {'eye': np.array([3., 4., 5.]), 'interest': np.array([2., 4., 5.]), 'upvector': np.array([0., 0., 1.])}
    return transform, values, expected


def edit(transform, values):
    for name, value in values.items():
        if isinstance(value, np.ndarray):
            getattr(transform, name)[:] = value
        else:
            setattr(transform, name, value)


def round_trip(mesh):
    stream = io.BytesIO()
    mesh.write(stream)
    return collada.Collada(io.BytesIO(stream.getvalue()), validate_output=True)


@pytest.mark.parametrize('kind', KINDS)
def test_direct_save_persists_edited_parameters(kind):
    transform, values, expected = transform_case(kind)
    transform.xmlnode.set('sid', 'placement')
    edit(transform, values)
    transform.save()
    reloaded = type(transform).load(collada.Collada(), etree.fromstring(etree.tostring(transform.xmlnode)))
    np.testing.assert_allclose(transform.matrix, expected, atol=1e-6)
    np.testing.assert_allclose(reloaded.matrix, expected, atol=1e-6)
    assert reloaded.xmlnode.get('sid') == 'placement'


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('changed', [False, True])
def test_document_write_updates_transform_and_geometry(kind, changed):
    transform, values, expected = transform_case(kind)
    original = transform.matrix.copy()
    vertices = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    mesh = collada.Collada(validate_output=True)
    source = collada.source.FloatSource('positions', vertices.ravel(), ('X', 'Y', 'Z'))
    geometry = collada.geometry.Geometry(mesh, 'triangle', 'Triangle', [source])
    inputs = collada.source.InputList()
    inputs.addInput(0, 'VERTEX', '#positions')
    geometry.primitives.append(geometry.createTriangleSet(np.array([0, 1, 2]), inputs, None))
    mesh.geometries.append(geometry)
    node = scene.Node('node', [scene.GeometryNode(geometry)], [transform])
    mesh.scene = scene.Scene('scene', [node])
    mesh.scenes.append(mesh.scene)
    mesh = round_trip(mesh)
    if changed:
        edit(mesh.scene.nodes[0].transforms[0], values)
    else:
        expected = original
    for _ in range(2):
        reloaded = round_trip(mesh)
        for document in (mesh, reloaded):
            np.testing.assert_allclose(document.scene.nodes[0].matrix, expected, atol=1e-6)
            primitive = next(next(document.scene.objects('geometry')).primitives())
            expected_vertices = vertices @ expected[:3, :3].T + expected[:3, 3]
            np.testing.assert_allclose(primitive.vertex, expected_vertices, atol=1e-6)
        mesh = reloaded


def test_node_save_combines_current_parameters_in_existing_order():
    translation = scene.TranslateTransform(0, 0, 0)
    scaling = scene.ScaleTransform(1, 1, 1)
    node = scene.Node('node', transforms=[translation, scaling])
    translation.x = 5
    scaling.y = 3
    node.save()
    expected = np.array([[1, 0, 0, 5], [0, 3, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    np.testing.assert_allclose(node.matrix, expected)
    mesh = collada.Collada(validate_output=True)
    mesh.scene = scene.Scene('scene', [node])
    mesh.scenes.append(mesh.scene)
    np.testing.assert_allclose(round_trip(mesh).scene.nodes[0].matrix, expected)
