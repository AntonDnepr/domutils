import pytest
from core.consts import ERAS
from domdata.models import Nation


@pytest.fixture
def initial_data_for_mapgen():
    assert Nation.find((Nation.name == "T'ien Ch'i")).all()
    assert Nation.find((Nation.name == "Tir na n'Og")).all()
    nation1 = [
        x
        for x in Nation.find((Nation.name == "Tir na n'Og")).all()
        if x.era == ERAS["EA"]
    ][0]
    nation2 = [
        x
        for x in Nation.find((Nation.name == "T'ien Ch'i")).all()
        if x.era == ERAS["EA"]
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
                    "id": "6a10c26a-96dc-49c4-9663-75151a3a609a",
                    "for_nation": "(EA) Tir na n'Og",
                    "quantity": 1,
                    "magic": {"fire": "2", "blood": "2"},
                },
                {
                    "dominions_id": "7",
                    "name": "Emerald Guard",
                    "id": "02d84d0c-1cbd-41ed-98a6-b5949010155d",
                    "for_nation": "(EA) T'ien Ch'i",
                    "quantity": 1,
                },
            ],
            "units": [
                {
                    "dominions_id": "105",
                    "name": "Woodhenge Druid",
                    "id": "dc5e61de-3747-46b0-bd33-b361cedc78d9",
                    "for_nation": "(EA) Tir na n'Og",
                    "quantity": "10",
                },
                {
                    "dominions_id": "408",
                    "name": "Water Elemental",
                    "id": "23925abc-40c0-4feb-9dcd-4b13d4d336a5",
                    "for_nation": "(EA) T'ien Ch'i",
                    "quantity": "10",
                },
            ],
        },
        nation1,
        nation2,
    )
