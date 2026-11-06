"""Camera property edits must preserve application metadata through public writes."""
import io

import pytest

import collada
from collada.common import tag
from collada.xmlutil import etree


NS = 'urn:camera-metadata-test'


def camera_scene(kind, metadata=True):
    dimension = 'xfov' if kind == 'perspective' else 'xmag'
    value = '45' if kind == 'perspective' else '2'
    extra = ('<extra id="camera-extra"><technique profile="TEST"><custom:note>original</custom:note>'
             '</technique></extra>') if metadata else ''
    asset = '<asset><created>2020-01-01T00:00:00</created><modified>2020-01-02T00:00:00</modified></asset>' if metadata else ''
    optics = ('<technique profile="LENS"><custom:lens>preserved</custom:lens></technique>'
              '<extra><technique profile="OPTICS"><custom:flag>1</custom:flag></technique></extra>') if metadata else ''
    imager = '<imager><technique profile="SENSOR"><custom:width>36</custom:width></technique></imager>' if metadata else ''
    xml = f'''<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" xmlns:custom="{NS}" version="1.4.1">
      <asset><created>2020-01-01T00:00:00</created><modified>2020-01-02T00:00:00</modified></asset>
      <library_cameras><camera id="camera" name="DisplayCamera">{asset}<optics><technique_common>
        <{kind}><{dimension} sid="horizontal">{value}</{dimension}><znear sid="near">0.1</znear><zfar sid="far">100</zfar></{kind}>
      </technique_common>{optics}</optics>{imager}{extra}</camera></library_cameras>
      <library_visual_scenes><visual_scene id="scene"><node id="node"><instance_camera url="#camera"/></node></visual_scene></library_visual_scenes>
      <scene><instance_visual_scene url="#scene"/></scene></COLLADA>'''
    mesh = collada.Collada(io.BytesIO(xml.encode()), validate_output=True)
    if mesh.validator is not None:
        assert mesh.validator.validate(etree.fromstring(xml.encode()))
    return mesh


def round_trip(mesh):
    output = io.BytesIO()
    mesh.write(output)
    return collada.Collada(io.BytesIO(output.getvalue()), validate_output=True)


@pytest.mark.parametrize('kind', ['perspective', 'orthographic'])
@pytest.mark.parametrize('edit', ['unchanged', 'value', 'axis', 'clip', 'id'])
def test_camera_metadata_survives_property_edits(kind, edit):
    mesh = camera_scene(kind)
    camera = mesh.cameras[0]
    x, y = ('xfov', 'yfov') if kind == 'perspective' else ('xmag', 'ymag')
    if edit == 'value':
        setattr(camera, x, 60 if kind == 'perspective' else 4)
    elif edit == 'axis':
        setattr(camera, x, None)
        setattr(camera, y, 30 if kind == 'perspective' else 3)
        camera.aspect_ratio = 2
    elif edit == 'clip':
        camera.znear, camera.zfar = 0.5, 500
    elif edit == 'id':
        camera.id = 'renamed-camera'
    expected = (camera.id, getattr(camera, x), getattr(camera, y), camera.aspect_ratio, camera.znear, camera.zfar)
    # Exercise the documented raw XML editing path for application metadata.
    camera.xmlnode.find(f"{tag('extra')}/{tag('technique')}/{{{NS}}}note").text = 'edited metadata'
    for _ in range(2):
        reloaded = round_trip(mesh)
        loaded = reloaded.cameras[0]
        assert (loaded.id, getattr(loaded, x), getattr(loaded, y), loaded.aspect_ratio, loaded.znear, loaded.zfar) == expected
        assert loaded.xmlnode.get('name') == 'DisplayCamera'
        assert loaded.xmlnode.find(tag('asset')) is not None
        assert loaded.xmlnode.find(f"{tag('extra')}/{tag('technique')}/{{{NS}}}note").text == 'edited metadata'
        optics = loaded.xmlnode.find(tag('optics'))
        assert optics.find(f"{tag('technique')}/{{{NS}}}lens").text == 'preserved'
        assert optics.find(f"{tag('extra')}/{tag('technique')}/{{{NS}}}flag").text == '1'
        assert loaded.xmlnode.find(f"{tag('imager')}/{tag('technique')}/{{{NS}}}width").text == '36'
        projection = optics.find(f"{tag('technique_common')}/{tag(kind)}")
        if edit != 'axis':
            assert projection.find(tag(x)).get('sid') == 'horizontal'
        assert projection.find(tag('znear')).get('sid') == 'near'
        assert projection.find(tag('zfar')).get('sid') == 'far'
        assert next(reloaded.scene.objects('camera')).original is loaded
        mesh, camera = reloaded, loaded


@pytest.mark.parametrize('kind', ['perspective', 'orthographic'])
def test_camera_without_extra_metadata_still_saves(kind):
    mesh = camera_scene(kind, metadata=False)
    mesh.cameras[0].zfar = 250
    assert round_trip(mesh).cameras[0].zfar == 250
