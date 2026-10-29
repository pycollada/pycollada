import io
from pathlib import Path
import tempfile
import unittest

import collada
import numpy
from collada.common import E, tag


class TestBumpmap(unittest.TestCase):
    def test_complete_scene_fixture(self):
        data_dir = Path(__file__).parent / 'data'
        document = collada.Collada(str(data_dir / 'bumpmap.dae'), validate_output=True)
        if document.validator is not None:
            self.assertTrue(document.validator.validate(document.xmlnode))
        image_data = {image.path: image.data for image in document.images}
        for data in image_data.values():
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))

        def check_scene(document, bump_image):
            geometries = list(document.scene.objects('geometry'))
            self.assertEqual(len(geometries), 1)
            primitives = list(geometries[0].primitives())
            self.assertEqual(len(primitives), 1)
            triangles = primitives[0]
            self.assertEqual(len(triangles), 1)
            numpy.testing.assert_array_equal(triangles[0].vertices,
                                             [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            numpy.testing.assert_array_equal(triangles[0].texcoords[0],
                                             [[0, 0], [1, 0], [0, 1]])
            self.assertEqual(triangles.inputmap, {'UV0': ('TEXCOORD', '0')})
            self.assertIs(triangles.material, document.materials['bump-material'])
            effect = triangles.material.effect
            self.assertEqual(effect.diffuse.texcoord, 'UV0')
            self.assertEqual(effect.diffuse.sampler.surface.image.id, 'diffuse-image')
            if bump_image is None:
                self.assertIsNone(effect.bumpmap)
                self.assertIsNone(effect.xmlnode.find('.//' + tag('bump')))
            else:
                self.assertIsNotNone(effect.bumpmap)
                self.assertEqual(effect.bumpmap.texcoord, 'UV0')
                self.assertEqual(effect.bumpmap.sampler.surface.image.id, bump_image)
                self.assertEqual(effect.xmlnode.find('.//' + tag('bump')).get('bumptype'),
                                 'NORMALMAP')
            for image in document.images:
                self.assertEqual(image.data, image_data[image.path])

        check_scene(document, 'normal-image')
        effect = document.effects['bump-effect']
        effect.bumpmap = collada.material.Map(effect.diffuse.sampler, 'UV0')
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for name, data in image_data.items():
                (directory / name).write_bytes(data)
            filename = str(directory / 'bumpmap.dae')
            for _ in range(2):
                document.write(filename)
                document = collada.Collada(filename, validate_output=True)
                check_scene(document, 'diffuse-image')
            document.effects['bump-effect'].bumpmap = None
            document.write(filename)
            document = collada.Collada(filename, validate_output=True)
            check_scene(document, None)

    def make_document(self):
        document = collada.Collada(validate_output=True)
        image = collada.material.CImage('image', 'bump.png')
        surface = collada.material.Surface('surface', image)
        sampler = collada.material.Sampler2D('sampler', surface)
        texture = collada.material.Map(sampler, 'UV0')
        effect = collada.material.Effect('effect', [surface, sampler], 'phong',
                                         diffuse=texture, bumpmap=texture)
        document.images.append(image)
        document.effects.append(effect)
        return document, effect

    def roundtrip(self, document):
        stream = io.BytesIO()
        document.write(stream)
        stream.seek(0)
        return collada.Collada(stream, validate_output=True)

    def test_new_bumpmap_roundtrip(self):
        document, effect = self.make_document()
        for _ in range(2):
            document = self.roundtrip(document)
            effect = document.effects['effect']
            self.assertIsNotNone(effect.bumpmap)
            self.assertEqual(effect.bumpmap.texcoord, 'UV0')
            self.assertEqual(effect.bumpmap.sampler.surface.image.path, 'bump.png')
            self.assertEqual(effect.diffuse.sampler.id, 'sampler')
            bumps = effect.xmlnode.findall('.//' + tag('bump'))
            self.assertEqual(len(bumps), 1)
            self.assertIsNone(effect.xmlnode.find('.//' + tag('phong') + '/' + tag('bump')))

    def test_edit_and_remove_loaded_bumpmap(self):
        document, effect = self.make_document()
        technique = effect.xmlnode.find(tag('profile_COMMON') + '/' + tag('technique'))
        extension = E.technique(E.bump(E.texture(texture='sampler', texcoord='UV0'),
                                       bumptype='NORMALMAP'),
                                E.custom('preserve me'), profile='FCOLLADA')
        technique.append(E.extra(extension))
        document = self.roundtrip(document)
        effect = document.effects['effect']
        effect.bumpmap.texcoord = 'UV1'
        document = self.roundtrip(document)
        effect = document.effects['effect']
        self.assertEqual(effect.bumpmap.texcoord, 'UV1')
        bump = effect.xmlnode.find('.//' + tag('bump'))
        self.assertEqual(bump.get('bumptype'), 'NORMALMAP')
        effect.bumpmap = None
        document = self.roundtrip(document)
        effect = document.effects['effect']
        self.assertIsNone(effect.bumpmap)
        self.assertIsNone(effect.xmlnode.find('.//' + tag('bump')))
        self.assertEqual(effect.xmlnode.find('.//' + tag('custom')).text, 'preserve me')
        self.assertEqual(effect.diffuse.texcoord, 'UV0')
