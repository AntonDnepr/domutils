import os.path

import requests


def load_units():
    """
    This function loads the units data from the BaseU.csv file located on the
    github repository.
    """
    url = (
        "https://raw.githubusercontent.com/larzm42/"
        "dom6inspector/main/gamedata/BaseU.csv"
    )
    response = requests.get(url)
    assert response.status_code == 200
    # build path to csvs/BaseU.csv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/BaseU.csv"), "w") as f:
        f.write(response.content.decode("utf-8"))


def load_nations():
    """
    This function loads the nations data from the nations.csv file located on the
    github repository.
    """
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


def load_required_data():
    load_units()
    load_nations()
