import pytest
from core.consts import INVERTED_ERAS
from domdata.models import Nation


@pytest.fixture
def initial_data_for_mapgen():
    assert Nation.find((Nation.name == "T'ien Ch'i")).all()
    assert Nation.find((Nation.name == "Tir na n'Og")).all()
    nation1 = [
        x
        for x in Nation.find((Nation.name == "Tir na n'Og")).all()
        if x.era == INVERTED_ERAS["EA"]
    ][0]
    nation2 = [
        x
        for x in Nation.find((Nation.name == "T'ien Ch'i")).all()
        if x.era == INVERTED_ERAS["EA"]
    ][0]
    return (
        {
            "land_nation_1": "(EA) Tir na n'Og",
            "land_nation_2": "(EA) T'ien Ch'i",
            "water_nation_1": "",
            "water_nation_2": "",
            "commanders": [
                {
                    "dominions_id": "1786",
                    "name": "Fir Bolg",
                    "for_nation": "(EA) Tir na n'Og",
                    "quantity": 1,
                    "magic": {"fire": "2", "blood": "2"},
                },
                {
                    "dominions_id": "7",
                    "name": "Emerald Guard",
                    "for_nation": "(EA) T'ien Ch'i",
                    "quantity": 1,
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
