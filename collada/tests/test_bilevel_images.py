"""Packed one-bit textures must expose full-sized, normalized pixel arrays."""

import io
from pathlib import Path

import numpy
import pytest

import collada

Image = pytest.importorskip('PIL.Image')


def png_data(mode, size, values):
    image = Image.new(mode, size)
    image.putdata(values)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


@pytest.mark.parametrize('width', [1, 3, 8, 9])
@pytest.mark.parametrize('height', [1, 2])
def test_bilevel_arrays(width, height):
    values = [255 if (row + col) % 2 == 0 else 0 for row in range(height) for col in range(width)]
    data = png_data('1', (width, height), values)
    image = collada.material.CImage('image', 'mono.png')
    image.data = data
    expected = numpy.array(values, dtype=numpy.uint8).reshape(height, width, 1)
    pixels = image.uintarray
    numpy.testing.assert_array_equal(pixels, expected)
    assert pixels.dtype == numpy.uint8
    assert image.uintarray is pixels
    numpy.testing.assert_array_equal(image.floatarray, expected.astype(numpy.float32) / 255)
    assert image.pilimage.mode == '1'
    assert image.data == data


@pytest.mark.parametrize('mode,values,expected', [
    ('L', [0, 255], [[[0], [255]]]),
    ('LA', [(20, 255), (40, 127)], [[[20, 255], [40, 127]]]),
    ('RGB', [(20, 40, 60), (80, 100, 120)], [[[20, 40, 60], [80, 100, 120]]]),
    ('RGBA', [(20, 40, 60, 255), (80, 100, 120, 127)], [[[20, 40, 60, 255], [80, 100, 120, 127]]]),
    ('P', [0, 1], [[[0], [1]]]),
])
def test_existing_pixel_modes(mode, values, expected):
    image = collada.material.CImage('image', 'control.png')
    image.data = png_data(mode, (2, 1), values)
    numpy.testing.assert_array_equal(image.uintarray, expected)
    assert image.pilimage.mode == mode


def test_replacing_data_invalidates_bilevel_caches():
    image = collada.material.CImage('image', 'image.png')
    image.data = png_data('1', (3, 1), [255, 0, 255])
    numpy.testing.assert_array_equal(image.floatarray, [[[1], [0], [1]]])
    image.data = png_data('RGB', (1, 1), [(10, 20, 30)])
    numpy.testing.assert_array_equal(image.uintarray, [[[10, 20, 30]]])
    assert image.pilimage.mode == 'RGB'


def test_bilevel_texture_scene_round_trip():
    fixture = Path(__file__).with_name('data') / 'bumpmap.dae'
    data = png_data('1', (3, 2), [255, 0, 255, 0, 255, 0])

    def loader(path):
        return data

    xml = fixture.read_bytes()
    for _ in range(2):
        mesh = collada.Collada(io.BytesIO(xml), aux_file_loader=loader, validate_output=True)
        image = mesh.materials[0].effect.diffuse.sampler.surface.image
        numpy.testing.assert_array_equal(image.floatarray[:, :, 0], [[1, 0, 1], [0, 1, 0]])
        assert len(list(next(mesh.scene.objects('geometry')).primitives())) == 1
        output = io.BytesIO()
        mesh.write(output)
        xml = output.getvalue()
