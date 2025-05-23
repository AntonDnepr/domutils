import pytest
from apps.domdata.parser import parse_dm_files, parse_units
from apps.mapgenerator.app import app
from apps.core.consts import TEST
from apps.core.redis import get_redis_client
from apps.domdata.models import Nation, Unit


@pytest.fixture(scope="module", autouse=True)
def generated_data():
    client = get_redis_client()
    pipeline = client.pipeline()
    unit1 = Unit(
        dominions_id=999999,
        name="TestMonster",
        mod=TEST,
    )
    unit1.save(pipeline=pipeline)
    unit2 = Unit(
        dominions_id=999998,
        name="AlohaMonster2",
        mod=TEST,
    )
    unit2.save(pipeline=pipeline)
    nation1 = Nation(
        dominions_id="000000",
        name="AlohaNation",
        era="3",
        mod=TEST,
    )
    nation1.save(pipeline=pipeline)
    nation2 = Nation(
        dominions_id="111111",
        name="MonsterNation",
        era="3",
        mod=TEST,
    )
    nation2.save(pipeline=pipeline)
    pipeline.execute()
    yield
    units = Unit.find(Unit.mod == TEST).all()
    for unit in units:
        unit.delete(pk=unit.pk, pipeline=pipeline)
    nations = Nation.find(Nation.mod == TEST).all()
    for nation in nations:
        nation.delete(pk=nation.pk, pipeline=pipeline)
    pipeline.execute()


def test_autocomplete_units_query():
    request, response = app.test_client.get(
        "/dom5/autocomplete/units/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "AlohaMonster2" in data


def test_autocomplete_units_empty_query():
    request, response = app.test_client.get("/dom5/autocomplete/units/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "table-responsive" not in data


def test_autocomplete_nations_query():
    request, response = app.test_client.get(
        "/dom5/autocomplete/nations/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "AlohaNation" in data


def test_autocomplete_nations_empty_query():
    request, response = app.test_client.get("/dom5/autocomplete/nations/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "table-responsive" not in data


def test_map_generation_view(initial_data_for_mapgen):
    parse_units()
    parse_dm_files()
    data, *_ = initial_data_for_mapgen
    request, response = app.test_client.post("/dom5/generate-map/", json=data)
    assert request.method.lower() == "post"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"
    assert response.headers["Content-Disposition"] == "attachment; filename=MyArena.map"
