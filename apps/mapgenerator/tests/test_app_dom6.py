import json
from urllib.parse import quote_plus

import pytest
from apps.core.consts import TEST
from apps.core.redis import get_redis_client
from apps.dom6data.models import Dom6Item, Dom6Nation, Dom6Unit
from apps.dom6data.parser import parse_dom6_dm_files, parse_dom6_units
from apps.mapgenerator.app import app


@pytest.fixture()
def generated_data():
    client = get_redis_client()
    pipeline = client.pipeline()
    unit1 = Dom6Unit(
        dominions_id=999999,
        name="Test Monster",
        mod=TEST,
        is_commander=False,
        slow_to_recruit=False,
    )
    unit1.save(pipeline=pipeline)
    unit2 = Dom6Unit(
        dominions_id=999998,
        name="AlohaMonster2",
        mod=TEST,
        is_commander=True,
        slow_to_recruit=False,
    )
    unit2.save(pipeline=pipeline)
    nation1 = Dom6Nation(
        dominions_id="000000",
        name="AlohaNation",
        era="3",
        mod=TEST,
    )
    nation1.save(pipeline=pipeline)
    unit1.nations_ids.append(nation1.pk)
    unit1.save(pipeline=pipeline)
    nation2 = Dom6Nation(
        dominions_id="111111",
        name="MonsterNation",
        era="3",
        mod=TEST,
    )
    nation2.save(pipeline=pipeline)
    item1 = Dom6Item(name="Test item of magic", mod=TEST)
    item1.save(pipeline=pipeline)
    item2 = Dom6Item(name="Garlic for vampires", mod=TEST)
    item2.save(pipeline=pipeline)
    pipeline.execute()


def test_dom6_autocomplete_units_query(generated_data):
    request, response = app.test_client.get(
        "/dom6/autocomplete/units/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "AlohaMonster2" in data


def test_dom6_autocomplete_units_by_id(generated_data):
    request, response = app.test_client.get(
        "/dom6/autocomplete/units/?search_term=999998&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "AlohaMonster2" in data


def test_dom6_autocomplete_units_empty_query(generated_data):
    request, response = app.test_client.get("/dom6/autocomplete/units/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "table-responsive" not in data


def test_dom6_autocomplete_nations_query(generated_data):
    request, response = app.test_client.get(
        "/dom6/autocomplete/nations/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "AlohaNation" in data


def test_dom6_autocomplete_nations_empty_query(generated_data):
    request, response = app.test_client.get("/dom6/autocomplete/nations/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "table-responsive" not in data


def test_dom6_map_generation_view(initial_dom6_data_for_mapgen):
    parse_dom6_units()
    parse_dom6_dm_files()
    data, *_ = initial_dom6_data_for_mapgen
    request, response = app.test_client.post("/dom6/generate-map/", json=data)
    assert request.method.lower() == "post"
    assert response.status == 200
    assert response.content_type == "application/zip; charset=utf-8"
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=CustomArena.zip"
    )


def test_dom6_map_generation_view_only_map(initial_dom6_data_for_mapgen):
    parse_dom6_units()
    parse_dom6_dm_files()
    data, *_ = initial_dom6_data_for_mapgen
    data["only_map"] = True
    request, response = app.test_client.post("/dom6/generate-map/", json=data)
    assert request.method.lower() == "post"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=CustomArena.map"
    )


def test_dom6_autocomplete_items_query(generated_data):
    request, response = app.test_client.get(
        "/dom6/autocomplete/items/?search_term=garlic&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "Garlic for vampires" in data


def test_dom6_autocomplete_items_empty_query(generated_data):
    request, response = app.test_client.get("/dom6/autocomplete/items/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = response.body.decode("utf-8")
    assert "table-responsive" not in data


def test_dom6_api_endpoint(generated_data):
    name = quote_plus("Test Monsters 22")
    request, response = app.test_client.get(f"/dom6/api/units/{name}?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = json.loads(response.body.decode("utf-8"))
    names = [x["name"] for x in data]
    assert "Test Monster" in names
    index = names.index("Test Monster")
    assert "AlohaNation" in [x["name"] for x in data[index]["nations"]]
