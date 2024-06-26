import os.path

import requests


def load_units():
    names = [
        "BaseU.csv",
        "coast_leader_types_by_nation.csv",
        "fort_leader_types_by_nation.csv",
        "nonfort_leader_types_by_nation.csv",
        "attributes_by_nation.csv",
        "coast_troop_types_by_nation.csv",
        "fort_troop_types_by_nation.csv",
        "nonfort_troop_types_by_nation.csv",
        "MagicSites.csv",
    ]
    for name in names:
        url = (
            "https://raw.githubusercontent.com/larzm42/"
            f"dom6inspector/main/gamedata/{name}"
        )
        response = requests.get(url)
        assert (
            response.status_code == 200
        ), f"{url} responded with {response.status_code}"
        # build path to csvs/BaseU.csv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, f"csvs/{name}"), "w") as f:
            f.write(response.content.decode("utf-8"))


def load_nations():
    url = (
        "https://raw.githubusercontent.com/larzm42/"
        "dom6inspector/main/gamedata/nations.csv"
    )
    response = requests.get(url)
    assert response.status_code == 200
    # build path to csvs/nations.csv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/nations.csv"), "w") as f:
        f.write(response.content.decode("utf-8"))


def load_inventory():
    url = (
        "https://raw.githubusercontent.com/larzm42/"
        "dom6inspector/main/gamedata/BaseI.csv"
    )
    response = requests.get(url)
    assert response.status_code == 200
    # build path to csvs/nations.csv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/BaseI.csv"), "w") as f:
        f.write(response.content.decode("utf-8"))


def load_required_data():
    load_units()
    load_nations()
    load_inventory()
