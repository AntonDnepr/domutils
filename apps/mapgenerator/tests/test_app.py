import json

from apps.mapgenerator.app import app


def test_autocomplete_units_query():
    request, response = app.test_client.get(
        "/autocomplete/units/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    data = json.loads(response.body.decode("utf-8"))
    assert len(data) == 1
    assert data[0]["name"] == "AlohaMonster2"


def test_autocomplete_units_empty_query():
    request, response = app.test_client.get("/autocomplete/units/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = json.loads(response.body.decode("utf-8"))
    assert len(data) == 0


def test_autocomplete_nations_query():
    request, response = app.test_client.get(
        "/autocomplete/nations/?search_term=Aloha&mods=test"
    )
    assert request.method.lower() == "get"
    assert response.status == 200
    data = json.loads(response.body.decode("utf-8"))
    assert len(data) == 1
    assert data[0]["name"] == "AlohaNation"


def test_autocomplete_nations_empty_query():
    request, response = app.test_client.get("/autocomplete/nations/?mods=test")
    assert request.method.lower() == "get"
    assert response.status == 200
    data = json.loads(response.body.decode("utf-8"))
    assert len(data) == 0
