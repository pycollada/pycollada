"""Edited transform stacks must have the same meaning after a scene round trip."""

import io

import numpy
import pytest

import collada
from collada.scene import GeometryNode, Node, ScaleTransform, Scene, TranslateTransform


@pytest.mark.parametrize('edit,expected', [
    ('unchanged', [[10, 0, 0], [12, 0, 0], [10, 3, 0]]),
    ('reverse', [[20, 0, 0], [22, 0, 0], [20, 3, 0]]),
    ('prepend', [[15, 0, 0], [17, 0, 0], [15, 3, 0]]),
    ('replace', [[5, 0, 0], [7, 0, 0], [5, 3, 0]]),
    ('remove', [[0, 0, 0], [2, 0, 0], [0, 3, 0]]),
    ('clear', [[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
])
def test_edited_transform_scene_round_trip(edit, expected):
    mesh = collada.Collada(validate_output=True)
    source = collada.source.FloatSource('positions', numpy.array([0, 0, 0, 1, 0, 0, 0, 1, 0]), ('X', 'Y', 'Z'))
    geometry = collada.geometry.Geometry(mesh, 'triangle', 'triangle', [source])
    inputs = collada.source.InputList()
    inputs.addInput(0, 'VERTEX', '#positions')
    geometry.primitives.append(geometry.createTriangleSet(numpy.array([0, 1, 2]), inputs, None))
    mesh.geometries.append(geometry)
    parent = Node('parent', children=[GeometryNode(geometry)],
                  transforms=[TranslateTransform(10, 0, 0), ScaleTransform(2, 3, 1)], name='KeptName')
    parent.xmlnode.set('sid', 'kept-sid')
    mesh.scene = Scene('scene', [parent])
    mesh.scenes.append(mesh.scene)
    # Start from loaded XML as well as a fresh Python scene.
    initial = io.BytesIO()
    mesh.write(initial)
    mesh = collada.Collada(io.BytesIO(initial.getvalue()), validate_output=True)
    parent = mesh.scene.nodes[0]
    if edit == 'reverse':
        parent.transforms.reverse()
    elif edit == 'prepend':
        parent.transforms.insert(0, TranslateTransform(5, 0, 0))
    elif edit == 'replace':
        parent.transforms[0] = TranslateTransform(5, 0, 0)
    elif edit == 'remove':
        parent.transforms.pop(0)
    elif edit == 'clear':
        parent.transforms.clear()
    # Repeated writes must be stable and preserve scene-node attributes.
    for _ in range(2):
        output = io.BytesIO()
        mesh.write(output)
        bound = next(mesh.scene.objects('geometry'))
        numpy.testing.assert_allclose(next(bound.primitives()).vertex, expected)
        mesh = collada.Collada(io.BytesIO(output.getvalue()), validate_output=True)
        bound = next(mesh.scene.objects('geometry'))
        numpy.testing.assert_allclose(next(bound.primitives()).vertex, expected)
        parent = mesh.scene.nodes[0]
        assert parent.name == 'KeptName'
        assert parent.xmlnode.get('sid') == 'kept-sid'


def test_saved_child_order_and_membership():
    children = [Node('first'), Node('second'), Node('third')]
    node = Node('parent', children=children[:])
    node.children[:] = [children[2], Node('new'), children[0]]
    node.save()
    assert [child.get('id') for child in node.xmlnode] == ['third', 'new', 'first']
    node.children.clear()
    node.save()
    assert list(node.xmlnode) == []
