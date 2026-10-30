"""List edits must preserve the named lookups used by document libraries."""

import io

import numpy
import pytest

import collada
from collada.util import IndexedList


class Item:
    def __init__(self, id, name):
        self.id, self.name = id, name


def check(items, expected, known):
    assert list(items) == expected
    for key in known:
        match = next((item for item in reversed(expected) if key in (item.id, item.name)), None)
        assert (key in items) == (match is not None)
        assert items.get(key) is match
        if match is not None:
            assert items[key] is match
        else:
            with pytest.raises(KeyError):
                items[key]


@pytest.mark.parametrize('operation', [
    'replace', 'replace-name', 'slice', 'extended-slice', 'delete', 'delete-name',
    'delete-slice', 'delete-extended', 'insert-end', 'insert-before', 'append',
    'extend', 'iadd', 'imul-zero', 'imul-two', 'clear', 'remove-object', 'remove-name',
    'pop', 'pop-name', 'reverse', 'sort',
])
def test_mutations_preserve_lookups(operation):
    a, b, c, d = [Item(name, name.upper()) for name in 'abcd']
    items = IndexedList([a, b, c], ('id', 'name'))
    expected = [a, b, c]
    if operation == 'replace':
        items[1] = d
        expected[1] = d
    elif operation == 'replace-name':
        items['b'] = d
        expected[1] = d
    elif operation == 'slice':
        items[1:] = [d]
        expected[1:] = [d]
    elif operation == 'extended-slice':
        items[::2] = [d, b]
        expected[::2] = [d, b]
    elif operation.startswith('delete'):
        index = {'delete': 1, 'delete-name': 'b', 'delete-slice': slice(None),
                 'delete-extended': slice(None, None, 2)}[operation]
        del items[index]
        del expected[1 if index == 'b' else index]
    elif operation.startswith('insert'):
        index = 3 if operation == 'insert-end' else 'b'
        items.insert(index, d)
        expected.insert(3 if index == 3 else 1, d)
    elif operation == 'append':
        items.append(d)
        expected.append(d)
    elif operation == 'extend':
        items.extend(iter([d]))
        expected.extend([d])
    elif operation == 'iadd':
        identity = items
        items += [d]
        assert items is identity
        expected += [d]
    elif operation.startswith('imul'):
        identity = items
        count = 0 if operation == 'imul-zero' else 2
        items *= count
        assert items is identity
        expected *= count
    elif operation == 'clear':
        items.clear()
        expected.clear()
    elif operation.startswith('remove'):
        assert items.remove(b if operation == 'remove-object' else 'b') is None
        expected.remove(b)
    elif operation.startswith('pop'):
        assert items.pop(1 if operation == 'pop' else 'b') is b
        expected.pop(1)
    elif operation == 'reverse':
        items.reverse()
        expected.reverse()
    elif operation == 'sort':
        items.sort(key=lambda item: item.id, reverse=True)
        expected.sort(key=lambda item: item.id, reverse=True)
    check(items, expected, list('abcdABCD'))


def test_slicing_preserves_indexed_lookup():
    a, b, c = [Item(name, name.upper()) for name in 'abc']
    items = IndexedList([a, b, c], ('id', 'name'))
    subset = items[::-1]
    assert isinstance(subset, IndexedList)
    check(subset, [c, b, a], list('abcABC'))


def test_duplicate_aliases_follow_remaining_list_order():
    first, second = Item('first', 'same'), Item('second', 'same')
    items = IndexedList([first, second], ('id', 'name'))
    items.reverse()
    assert items['same'] is first
    items.remove(first)
    assert items['same'] is second
    items.insert(0, first)
    assert items['same'] is second


@pytest.mark.parametrize('operation', ['replace', 'extend', 'append', 'slice-length', 'missing-remove'])
def test_failed_edits_preserve_list_and_lookup(operation):
    item = Item('a', 'A')
    items = IndexedList([item], ('id', 'name'))
    with pytest.raises((AttributeError, ValueError)):
        if operation == 'replace':
            items[0] = object()
        elif operation == 'extend':
            items.extend([Item('b', 'B'), object()])
        elif operation == 'append':
            items.append(object())
        elif operation == 'slice-length':
            items[::2] = []
        else:
            items.remove(Item('missing', 'MISSING'))
    check(items, [item], list('abAB'))


def test_document_library_removal_and_replacement_round_trip():
    mesh = collada.Collada(validate_output=True)
    source = collada.source.FloatSource('positions', numpy.array([0, 0, 0, 1, 0, 0, 0, 1, 0]), ('X', 'Y', 'Z'))
    original = collada.geometry.Geometry(mesh, 'old', 'Old', [source])
    replacement = collada.geometry.Geometry(mesh, 'replacement', 'Replacement', [source])
    inputs = collada.source.InputList()
    inputs.addInput(0, 'VERTEX', '#positions')
    replacement.primitives.append(replacement.createTriangleSet(numpy.array([0, 1, 2]), inputs, None))
    mesh.geometries.append(original)
    mesh.geometries.remove('old')
    assert not mesh.geometries and mesh.geometries.get('old') is None
    mesh.geometries += [original]
    mesh.geometries[:] = [replacement]
    assert mesh.geometries['replacement'] is replacement
    assert mesh.geometries.get('old') is None
    mesh.scene = collada.scene.Scene('scene', [collada.scene.Node('node', [collada.scene.GeometryNode(replacement)])])
    mesh.scenes.append(mesh.scene)
    output = io.BytesIO()
    mesh.write(output)
    reloaded = collada.Collada(io.BytesIO(output.getvalue()), validate_output=True)
    assert list(reloaded.geometries) == [reloaded.geometries['replacement']]
    assert next(reloaded.scene.objects('geometry')).original is reloaded.geometries['replacement']
