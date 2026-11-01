"""Relative image URIs must locate the same files on disk and in a ZAE archive."""

import io
from pathlib import Path
import zipfile

import pytest

import collada
from collada.common import DaeBrokenRefError


DATA = Path(__file__).with_name('data')


@pytest.mark.parametrize('backend', ['disk', 'zip'])
@pytest.mark.parametrize('filename,uri', [
    ('diffuse map.png', 'diffuse%20map.png'),
    ('café.png', 'caf%C3%A9.png'),
    ('hash#.png', 'hash%23.png'),
    ('literal%20.png', 'literal%2520.png'),
    ('nested dir/texture.png', 'nested%20dir/texture.png'),
    ('plus+name.png', 'plus+name.png'),
    ('plain.png', 'plain.png'),
])
def test_image_uri_scene_round_trip(tmp_path, backend, filename, uri):
    xml = (DATA / 'bumpmap.dae').read_bytes().replace(b'bumpmap-diffuse.png', uri.encode())
    diffuse = (DATA / 'bumpmap-diffuse.png').read_bytes()
    normal = (DATA / 'bumpmap-normal.png').read_bytes()

    def load_scene(document):
        if backend == 'disk':
            path = tmp_path / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(diffuse)
            (tmp_path / 'bumpmap-normal.png').write_bytes(normal)
            scene = tmp_path / 'scene.dae'
            scene.write_bytes(document)
            return collada.Collada(str(scene), validate_output=True)
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('models/scene.dae', document)
            archive.writestr('models/' + filename, diffuse)
            archive.writestr('models/bumpmap-normal.png', normal)
        return collada.Collada(io.BytesIO(output.getvalue()), zip_filename='models/scene.dae', validate_output=True)

    for _ in range(2):
        mesh = load_scene(xml)
        try:
            image = mesh.images['diffuse-image']
            assert image.path == uri
            assert image.data == diffuse
            assert image.pilimage.size == (1, 1)
            assert mesh.materials[0].effect.diffuse.sampler.surface.image is image
            assert len(list(next(mesh.scene.objects('geometry')).primitives())) == 1
            output = io.BytesIO()
            mesh.write(output)
            xml = output.getvalue()
            assert mesh.images['diffuse-image'].path == uri
        finally:
            if mesh.zfile is not None:
                mesh.zfile.close()


def test_custom_loader_receives_original_uri():
    uri = 'diffuse%20map.png'
    xml = (DATA / 'bumpmap.dae').read_bytes().replace(b'bumpmap-diffuse.png', uri.encode())
    expected = (DATA / 'bumpmap-diffuse.png').read_bytes()
    seen = []

    def loader(path):
        seen.append(path)
        return expected if path == uri else None

    mesh = collada.Collada(io.BytesIO(xml), aux_file_loader=loader)
    assert mesh.images['diffuse-image'].data == expected
    assert seen == [uri]


@pytest.mark.parametrize('backend', ['disk', 'zip'])
def test_missing_escaped_image_keeps_error_policy(tmp_path, backend):
    xml = (DATA / 'bumpmap.dae').read_bytes()
    if backend == 'disk':
        scene = tmp_path / 'scene.dae'
        scene.write_bytes(xml)
        mesh = collada.Collada(str(scene))
    else:
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('scene.dae', xml)
        mesh = collada.Collada(io.BytesIO(output.getvalue()))
    try:
        with pytest.raises(DaeBrokenRefError):
            mesh.getFileData('missing%20image.png')
    finally:
        if mesh.zfile is not None:
            mesh.zfile.close()
