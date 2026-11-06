"""Asset writes must save edited attribution and preserve contributor element order."""
import io

import pytest

import collada
from collada.asset import Contributor
from collada.common import tag


FIELDS = ('author', 'authoring_tool', 'comments', 'copyright', 'source_data')
VALUES = ('Alice', 'Editor 1', 'Original comment', 'Copyright Alice', 'source.dae')


def round_trip(mesh):
    stream = io.BytesIO()
    mesh.write(stream)
    return collada.Collada(io.BytesIO(stream.getvalue()), validate_output=True)


@pytest.mark.parametrize('field', FIELDS)
@pytest.mark.parametrize('operation', ['replace', 'remove', 'add'])
def test_document_saves_edited_contributor(field, operation):
    mesh = collada.Collada(validate_output=True)
    values = dict(zip(FIELDS, VALUES))
    if operation == 'add':
        values[field] = None
    mesh.assetInfo.contributors = [Contributor(**values), Contributor(author='Unchanged')]
    mesh = round_trip(mesh)
    original_created = mesh.assetInfo.created
    expected = None if operation == 'remove' else 'updated.dae' if field == 'source_data' else 'Updated value'
    setattr(mesh.assetInfo.contributors[0], field, expected)
    values[field] = expected
    for _ in range(2):
        mesh = round_trip(mesh)
        assert [getattr(mesh.assetInfo.contributors[0], name) for name in FIELDS] == [values[name] for name in FIELDS]
        assert mesh.assetInfo.contributors[1].author == 'Unchanged'
        assert mesh.assetInfo.created == original_created
        assert [node.tag for node in mesh.assetInfo.contributors[0].xmlnode] == [tag(name) for name in FIELDS if values[name] is not None]


def test_direct_contributor_save_inserts_earlier_fields_in_schema_order():
    mesh = collada.Collada(validate_output=True)
    contributor = Contributor(source_data='source.dae')
    mesh.assetInfo.contributors = [contributor]
    contributor.author = 'Alice'
    contributor.copyright = 'Copyright Alice'
    contributor.save()
    assert [node.tag for node in contributor.xmlnode] == [tag(name) for name in ('author', 'copyright', 'source_data')]
    assert round_trip(mesh).assetInfo.contributors[0].author == 'Alice'


def test_unchanged_contributors_round_trip():
    mesh = collada.Collada(validate_output=True)
    mesh.assetInfo.contributors = [Contributor(**dict(zip(FIELDS, VALUES))), Contributor()]
    reloaded = round_trip(mesh)
    assert [getattr(reloaded.assetInfo.contributors[0], name) for name in FIELDS] == list(VALUES)
    assert len(reloaded.assetInfo.contributors) == 2
