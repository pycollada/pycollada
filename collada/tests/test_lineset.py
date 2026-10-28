import io

import numpy
from numpy.testing import assert_array_equal
import unittest

import collada
from collada.xmlutil import etree
from collada.common import DaeIncompleteError, DaeMalformedError, E

fromstring = etree.fromstring
tostring = etree.tostring


class TestLineset(unittest.TestCase):

    def setUp(self):
        self.dummy = collada.Collada(validate_output=True)

    def test_lineset_construction(self):
        # An empty sources dict should raise an exception.
        with self.assertRaises(DaeIncompleteError) as e:
            collada.lineset.LineSet({}, None, None)
        self.assertIn("at least one", e.exception.msg)

        # As should passing one without VERTEX defined as a key.
        with self.assertRaises(DaeIncompleteError) as e:
            collada.lineset.LineSet({"a": []}, None, None)
        self.assertIn("requires vertex", e.exception.msg)

        # Adding an input list with vertex defined, but empty should raise an error.
        with self.assertRaises(DaeIncompleteError) as e:
            collada.lineset.LineSet({'VERTEX': []}, None, None)
        self.assertIn("requires vertex", e.exception.msg)

    def test_empty_lineset_saving(self):
        linefloats = [1, 1, -1, 1, -1, -1, -1, -0.9999998, -1, -0.9999997, 1, -1, 1, 0.9999995, 1, 0.9999994, -1.000001, 1]
        linefloatsrc = collada.source.FloatSource("mylinevertsource", numpy.array(linefloats), ('X', 'Y', 'Z'))
        geometry = collada.geometry.Geometry(self.dummy, "geometry0", "mygeometry", [linefloatsrc])
        input_list = collada.source.InputList()
        input_list.addInput(0, 'VERTEX', "#mylinevertsource")
        indices = numpy.array([0, 1, 1, 2, 2, 3, 3, 4, 4, 5])
        lineset = geometry.createLineSet(indices, input_list, "mymaterial")
        expected_indices = numpy.array([[[0], [1]], [[1], [2]], [[2], [3]], [[3], [4]], [[4], [5]]])
        # Check the initial values for the lineset.
        self.assertIsNotNone(str(lineset))
        assert_array_equal(lineset.index, expected_indices)
        self.assertEqual(lineset.nlines, len(expected_indices))
        self.assertEqual(lineset.material, "mymaterial")

        # Serialize and deserialize.
        lineset.save()
        loaded_lineset = collada.lineset.LineSet.load(collada, {'mylinevertsource': linefloatsrc}, fromstring(tostring(lineset.xmlnode)))

        # Check that the deserialized version has all of the same properties.
        self.assertEqual(loaded_lineset.sources, lineset.sources)
        self.assertEqual(loaded_lineset.material, lineset.material)
        assert_array_equal(loaded_lineset.index, lineset.index)
        assert_array_equal(loaded_lineset.indices, lineset.indices)
        self.assertEqual(loaded_lineset.nindices, lineset.nindices)
        self.assertEqual(loaded_lineset.nlines, lineset.nlines)

    def linestrip_document(self, strips):
        positions = collada.source.FloatSource('positions', numpy.arange(18), ('X', 'Y', 'Z'))
        normals = collada.source.FloatSource('normals', numpy.arange(18), ('X', 'Y', 'Z'))
        uv0 = collada.source.FloatSource('uv0', numpy.arange(12), ('S', 'T'))
        uv1 = collada.source.FloatSource('uv1', numpy.arange(12) + 20, ('S', 'T'))
        geometry = collada.geometry.Geometry(self.dummy, 'geometry', 'lines', [positions, normals, uv0, uv1])
        node = E.linestrips(
            E.input(semantic='VERTEX', source='#positions-vertices', offset='0'),
            E.input(semantic='NORMAL', source='#normals', offset='2'),
            E.input(semantic='TEXCOORD', source='#uv0', offset='3', set='0'),
            E.input(semantic='TEXCOORD', source='#uv1', offset='4', set='1'),
            count=str(len(strips)), material='wire', name='outlines')
        for strip in strips:
            node.append(E.p(' '.join(str(i) for vertex in strip for i in vertex)))
        geometry.xmlnode.find(collada.tag('mesh')).append(node)
        self.dummy.save()
        self.dummy.xmlnode.getroot().insert(1, E.library_geometries(geometry.xmlnode))
        return tostring(self.dummy.xmlnode.getroot())

    def test_linestrips_attributes_and_boundaries(self):
        # Offset 1 is unused; normals and both UV sets use independent indices.
        a, b, c = (0, 0, 1, 2, 3), (1, 0, 2, 3, 4), (2, 0, 3, 4, 5)
        d, e = (4, 0, 4, 0, 1), (5, 0, 5, 1, 2)
        document = self.linestrip_document([[a, b, c, a], [d, e]])
        mesh = collada.Collada(io.BytesIO(document))
        lines = mesh.geometries[0].primitives[0]
        expected = numpy.array([[a, b], [b, c], [c, a], [d, e]])
        self.assertIsInstance(lines, collada.lineset.LineSet)
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines.material, 'wire')
        assert_array_equal(lines.index, expected)
        assert_array_equal(lines.vertex_index, expected[:, :, 0])
        assert_array_equal(lines.normal_index, expected[:, :, 2])
        for i in range(2):
            assert_array_equal(lines.texcoord_indexset[i], expected[:, :, i + 3])
        for i, line in enumerate(lines):
            assert_array_equal(line.vertices, lines.vertex[expected[i, :, 0]])
            assert_array_equal(line.normals, lines.normal[expected[i, :, 2]])
            for j in range(2):
                assert_array_equal(line.texcoords[j], lines.texcoordset[j][expected[i, :, j + 3]])

        # Binding continues to use the existing line transform and material API.
        effect = collada.material.Effect('effect', [], 'lambert', diffuse=(1, 0, 0, 1))
        material = collada.material.Material('material', 'red', effect)
        matnode = collada.scene.MaterialNode('wire', material, inputs=[])
        matrix = numpy.eye(4)
        matrix[:3, 3] = [10, 20, 30]
        bound = lines.bind(matrix, {'wire': matnode})
        self.assertEqual(len(list(bound.lines())), 4)
        self.assertIs(bound.material, material)
        assert_array_equal(bound[0].vertices, lines[0].vertices + [10, 20, 30])
        assert_array_equal(bound[0].normals, lines[0].normals)
        assert_array_equal(bound[0].texcoords[1], lines[0].texcoords[1])

    def test_linestrips_roundtrip(self):
        a, b, c = (0, 0, 1, 2, 3), (1, 0, 2, 3, 4), (2, 0, 3, 4, 5)
        document = self.linestrip_document([[a, b, c], [c, a]])
        mesh = collada.Collada(io.BytesIO(document), validate_output=True)
        output = io.BytesIO()
        mesh.write(output)
        loaded = collada.Collada(io.BytesIO(output.getvalue()))
        lines = loaded.geometries[0].primitives[0]
        assert_array_equal(lines.index, mesh.geometries[0].primitives[0].index)
        self.assertEqual(lines.xmlnode.tag, collada.tag('linestrips'))
        self.assertEqual(lines.xmlnode.get('count'), '2')
        self.assertEqual(lines.xmlnode.get('name'), 'outlines')
        self.assertEqual(lines.xmlnode.get('material'), 'wire')
        original = fromstring(document).find('.//' + collada.tag('linestrips'))
        self.assertEqual([p.text for p in lines.xmlnode.findall(collada.tag('p'))],
                         [p.text for p in original.findall(collada.tag('p'))])

    def test_empty_linestrips(self):
        for strips in ([], [[]], [[(0, 0, 1, 2, 3)]]):
            with self.subTest(strips=strips):
                mesh = collada.Collada(io.BytesIO(self.linestrip_document(strips)))
                lines = mesh.geometries[0].primitives[0]
                self.assertEqual(len(lines), 0)
                self.assertEqual(lines.index.shape, (0, 2, 5))

    def test_malformed_linestrips(self):
        document = self.linestrip_document([[(0, 0, 1, 2, 3), (1, 0, 2, 3, 4)]])
        for text in ('0 0 1', '0 0 invalid 2 3'):
            with self.subTest(text=text):
                root = fromstring(document)
                root.find('.//' + collada.tag('p')).text = text
                with self.assertRaises(DaeMalformedError):
                    collada.Collada(io.BytesIO(tostring(root)))

    def test_linestrips_require_vertices(self):
        root = fromstring(self.linestrip_document([[(0, 0, 1, 2, 3), (1, 0, 2, 3, 4)]]))
        node = root.find('.//' + collada.tag('linestrips'))
        node.remove(node.find(collada.tag('input')))
        with self.assertRaises(DaeIncompleteError):
            collada.Collada(io.BytesIO(tostring(root)))

    def test_linestrips_vertex_only(self):
        root = fromstring(self.linestrip_document([[], []]))
        node = root.find('.//' + collada.tag('linestrips'))
        for inputnode in node.findall(collada.tag('input'))[1:]:
            node.remove(inputnode)
        pnodes = node.findall(collada.tag('p'))
        pnodes[0].text, pnodes[1].text = '0 1 2 0', '4 5'
        mesh = collada.Collada(io.BytesIO(tostring(root)))
        lines = mesh.geometries[0].primitives[0]
        assert_array_equal(lines.vertex_index, [[0, 1], [1, 2], [2, 0], [4, 5]])
        self.assertIsNone(lines[0].normals)
        self.assertEqual(len(lines[0].texcoords), 0)

    def test_independent_lines_stay_independent(self):
        a, b, c, d = (0, 0, 1, 2, 3), (1, 0, 2, 3, 4), (2, 0, 3, 4, 5), (4, 0, 4, 0, 1)
        root = fromstring(self.linestrip_document([[a, b, c, d]]))
        node = root.find('.//' + collada.tag('linestrips'))
        node.tag = collada.tag('lines')
        node.set('count', '2')
        mesh = collada.Collada(io.BytesIO(tostring(root)))
        lines = mesh.geometries[0].primitives[0]
        assert_array_equal(lines.index, [[a, b], [c, d]])


if __name__ == '__main__':
    unittest.main()
