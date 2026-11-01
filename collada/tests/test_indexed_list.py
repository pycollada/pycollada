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
        match = next((item for item in reversed(expected) if key == item.id), None)
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
    'extend', 'iadd', 'clear', 'remove-object',
    'pop', 'pop-name', 'reverse',
])
def test_mutations_preserve_lookups(operation):
    a, b, c, d = [Item(name, name.upper()) for name in 'abcd']
    items = IndexedList([a, b, c], ('id',))
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
    elif operation == 'clear':
        items.clear()
        expected.clear()
    elif operation.startswith('remove'):
        assert items.remove(b) is None
        expected.remove(b)
    elif operation.startswith('pop'):
        assert items.pop(1 if operation == 'pop' else 'b') is b
        expected.pop(1)
    elif operation == 'reverse':
        items.reverse()
        expected.reverse()
    check(items, expected, list('abcdABCD'))


def test_slicing_preserves_indexed_lookup():
    a, b, c = [Item(name, name.upper()) for name in 'abc']
    items = IndexedList([a, b, c], ('id',))
    subset = items[::-1]
    assert isinstance(subset, IndexedList)
    check(subset, [c, b, a], list('abcABC'))


def test_duplicate_ids_follow_remaining_list_order():
    first, second = Item('same', 'first'), Item('same', 'second')
    items = IndexedList([first, second], ('id',))
    assert items['same'] is second
    items.reverse()
    assert items['same'] is first
    items.remove(first)
    assert items['same'] is second
    items.insert(0, first)
    assert items['same'] is second


def test_failed_slice_and_remove_preserve_items():
    item = Item('a', 'A')
    items = IndexedList([item], ('id',))
    assert items['a'] is item
    with pytest.raises(ValueError):
        items[::2] = []
    with pytest.raises(ValueError):
        items.remove(Item('missing', 'MISSING'))
    check(items, [item], ['a', 'missing'])


def test_document_library_removal_and_replacement_round_trip():
    mesh = collada.Collada(validate_output=True)
    source = collada.source.FloatSource('positions', numpy.array([0, 0, 0, 1, 0, 0, 0, 1, 0]), ('X', 'Y', 'Z'))
    original = collada.geometry.Geometry(mesh, 'old', 'Old', [source])
    replacement = collada.geometry.Geometry(mesh, 'replacement', 'Replacement', [source])
    inputs = collada.source.InputList()
    inputs.addInput(0, 'VERTEX', '#positions')
    replacement.primitives.append(replacement.createTriangleSet(numpy.array([0, 1, 2]), inputs, None))
    mesh.geometries.append(original)
    mesh.geometries.remove(original)
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


def test_lazy_cache_and_incremental_loading():
    from collections.abc import MutableSequence

    a, b, c = [Item(name, name.upper()) for name in 'abc']
    items = IndexedList([a], ('id',))
    assert isinstance(items, MutableSequence) and not isinstance(items, list)
    assert items._by_id is None
    items.append(b)
    assert items._by_id is None
    assert items['a'] is a
    cache = items._by_id
    items.extend([c])
    assert items._by_id is cache and items['c'] is c
    items.append(a)
    assert items._by_id is cache
    items[0] = b
    assert items._by_id is None
    assert items['a'] is a


def test_self_extension_and_list_equality():
    a, b = Item('a', 'A'), Item('b', 'B')
    items = IndexedList([a, b], ('id',))
    assert items == [a, b] and [a, b] == items
    assert items == IndexedList([a, b], ('id',))
    assert items != [b, a] and items != (a, b)
    items.extend(items)
    assert items == [a, b, a, b]
    items += items
    assert items == [a, b, a, b] * 2
    assert items['a'] is a
    items.clear()
    assert items == [] and items.get('a') is None


def test_integer_ids_do_not_override_positions():
    first, second = Item(1, 'first'), Item(0, 'second')
    items = IndexedList([first, second], ('id',))
    assert items[0] is first and items[1] is second
    del items[0]
    assert items[0] is second
    with pytest.raises(IndexError):
        items[1]
    with pytest.raises(TypeError):
        items[1.5]
