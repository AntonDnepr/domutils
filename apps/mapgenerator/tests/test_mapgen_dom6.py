import copy
from unittest import mock

import pytest
from core.consts import INVERTED_ERAS, LAND_STARTS, WATER_STARTS
from dom6data.models import Dom6Nation
from dom6data.parser import parse_dom6_dm_files, parse_dom6_units
from mapgenerator.mapgen import dom6_data_into_map, dom6_process_data, dom6_substitute


@pytest.fixture(scope="module")
def parse_data_process():
    parse_dom6_units()
    parse_dom6_dm_files()


def test_dom6_generate_map_serializer_processed_data(initial_dom6_data_for_mapgen):
    data, nation1, nation2 = initial_dom6_data_for_mapgen
    returned_data = dom6_process_data(data)
    assert returned_data == [
        {
            nation1.dominions_id: [
                {
                    "1786": {
                        "magic": {
                            "mag_fire": "2",
                            "mag_blood": "2",
                            "mag_glamour": "3",
                        },
                        "units": [("105", "10")],
                        "items": ["Frost brand", "Ring of Fire"],
                    }
                }
            ],
            "land_type": "land",
        },
        {
            nation2.dominions_id: [{"7": {"units": [("408", "10")]}}],
            "land_type": "land",
        },
    ]


def test_dom6_mapgenerator_function(initial_dom6_data_for_mapgen):
    data, nation1, nation2 = initial_dom6_data_for_mapgen
    start1, start2 = LAND_STARTS
    returned_data = dom6_process_data(data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    assert len(mapgenerated_text) == 2
    assert mapgenerated_text[0] == (
        (
            "\n#allowedplayer {0}\n#specstart {0} {1}\n#setland {1}\n#commander 1786\n"
            "#units 10 105\n#clearmagic\n#mag_fire 2\n#mag_blood 2\n#mag_glamour 3\n"
            '#additem "Frost brand"\n#additem "Ring of Fire"'
        ).format(nation1.dominions_id, start1)
    )
    assert mapgenerated_text[1] == (
        (
            "\n#allowedplayer {0}\n#specstart {0} {1}\n#setland {1}"
            "\n#commander 7\n#units 10 408"
        ).format(nation2.dominions_id, start2)
    )


@pytest.fixture
def data_for_mapgen_uw():
    assert Dom6Nation.find((Dom6Nation.name == "T'ien Ch'i")).all()
    assert Dom6Nation.find((Dom6Nation.name == "Tir na n'Og")).all()
    nation1 = [
        x
        for x in Dom6Nation.find((Dom6Nation.name == "Tir na n'Og")).all()
        if x.era == INVERTED_ERAS["EA"]
    ][0]
    nation2 = [
        x
        for x in Dom6Nation.find((Dom6Nation.name == "T'ien Ch'i")).all()
        if x.era == INVERTED_ERAS["EA"]
    ][0]
    return (
        {
            "water_nation_1": "(EA) Tir na n'Og",
            "water_nation_2": "(EA) T'ien Ch'i",
            "land_nation_1": "",
            "land_nation_2": "",
            "commanders": [
                {
                    "dominions_id": "1786",
                    "name": "Fir Bolg",
                    "for_nation": "(EA) Tir na n'Og",
                    "magic": {"fire": "2", "blood": "2"},
                },
                {
                    "dominions_id": "7",
                    "name": "Emerald Guard",
                    "for_nation": "(EA) T'ien Ch'i",
                },
            ],
            "units": [
                {
                    "dominions_id": "105",
                    "name": "Woodhenge Druid",
                    "for_nation": "(EA) Tir na n'Og",
                    "quantity": "10",
                },
                {
                    "dominions_id": "408",
                    "name": "Water Elemental",
                    "for_nation": "(EA) T'ien Ch'i",
                    "quantity": "10",
                },
            ],
        },
        nation1,
        nation2,
    )


def test_dom6_generate_map_serializer_processed_data_with_water_nation(
    data_for_mapgen_uw,
):
    data, nation3, nation4 = data_for_mapgen_uw
    returned_data = dom6_process_data(data)
    assert returned_data == [
        {
            nation3.dominions_id: [
                {
                    "1786": {
                        "magic": {"mag_fire": "2", "mag_blood": "2"},
                        "units": [("105", "10")],
                    }
                }
            ],
            "land_type": "water",
        },
        {
            nation4.dominions_id: [{"7": {"units": [("408", "10")]}}],
            "land_type": "water",
        },
    ]


def test_dom6_mapgenerator_function_with_water_nation(data_for_mapgen_uw):
    data, nation3, nation4 = data_for_mapgen_uw
    start1, start2 = WATER_STARTS
    returned_data = dom6_process_data(data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    assert len(mapgenerated_text) == 2
    assert mapgenerated_text[0] == (
        (
            "\n#allowedplayer {0}\n#specstart {0} {1}\n#setland {1}"
            "\n#commander 1786\n#units 10 105\n#clearmagic\n#mag_fire 2\n#mag_blood 2"
        ).format(nation3.dominions_id, start1)
    )
    assert mapgenerated_text[1] == (
        (
            "\n#allowedplayer {0}\n#specstart {0} {1}\n#setland {1}"
            "\n#commander 7\n#units 10 408"
        ).format(nation4.dominions_id, start2)
    )


def test_dom6_insert_data_into_template(initial_dom6_data_for_mapgen):
    data, *other = initial_dom6_data_for_mapgen
    returned_data = dom6_process_data(data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    final_map = dom6_substitute(data, mapgenerated_text)
    assert mapgenerated_text[0] in final_map
    assert mapgenerated_text[1] in final_map
    assert "$nation3" not in final_map
    assert "$nation4" not in final_map


def test_dom6_insert_uw_data_into_template(data_for_mapgen_uw):
    data, nation1, nation2 = data_for_mapgen_uw
    returned_data = dom6_process_data(data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    final_map = dom6_substitute(data, mapgenerated_text)
    assert mapgenerated_text[0] in final_map
    assert mapgenerated_text[1] in final_map
    assert "$nation3" not in final_map
    assert "$nation4" not in final_map


def test_dom6_map_with_cave(initial_dom6_data_for_mapgen):
    data, *other = initial_dom6_data_for_mapgen
    data_with_cave = copy.deepcopy(data)
    data_with_cave["use_cave_map"] = True
    returned_data = dom6_process_data(data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    mocked_open_function = mock.mock_open(read_data="")
    with mock.patch("mapgenerator.mapgen.open", mocked_open_function) as mocked:
        dom6_substitute(data, mapgenerated_text, use_cave_map=True)
        mocked.assert_called_once_with("apps/domdata/mapfiles/Arena_with_cave.map", "r")
