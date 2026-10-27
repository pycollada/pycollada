import io
import unittest

import collada
from collada.common import E, tag


class TestBumpmap(unittest.TestCase):
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
