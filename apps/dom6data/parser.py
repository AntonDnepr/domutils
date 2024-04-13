import csv
import glob
import os
import re

from apps.core.consts import DEBUG
from apps.core.redis import get_redis_client
from .models import Dom6Item, Dom6Nation, Dom6Unit


def parse_dom6_units():
    client = get_redis_client()
    pipeline = client.pipeline()
    unit_ids = Dom6Unit.all_pks()
    [Dom6Unit.delete(unit_id, pipeline=pipeline) for unit_id in unit_ids]
    pipeline.execute()
    nation_ids = Dom6Nation.all_pks()
    [Dom6Nation.delete(nation_id, pipeline=pipeline) for nation_id in nation_ids]
    pipeline.execute()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/BaseU.csv"), "r", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            unit = Dom6Unit(name=row["name"], dominions_id=row["id"])
            unit.save(pipeline=pipeline)
    pipeline.execute()

    with open(
        os.path.join(current_dir, "csvs/nations.csv"), "r", newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            # file contains some internal or not functional nations
            if row["era"] == "0":
                continue
            nation = Dom6Nation(
                name=row["name"], dominions_id=row["id"], era=row["era"]
            )
            nation.save(pipeline=pipeline)
    pipeline.execute()
    pipeline.reset()


def parse_dom6_dm_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_parse = glob.glob(os.path.join(current_dir, "mods/*.dm"))
    pipeline = get_redis_client().pipeline()
    try:
        units = Dom6Unit.find(Dom6Unit.mod == DEBUG).all()
        [Dom6Unit.delete(unit.pk, pipeline=pipeline) for unit in units]
        pipeline.execute()
        nations = Dom6Nation.find(Dom6Nation.mod == DEBUG)
        [Dom6Nation.delete(nation.pk, pipeline=pipeline) for nation in nations]
        pipeline.execute()
    except Exception as e:
        print(e)
        pass
    for dmfile in files_to_parse:
        with open(dmfile, "r") as file_content:
            new_nation, new_monster = False, False
            monster_id, monster_name = "", ""
            nation_id, nation_name, nation_era = "", "", ""
            mod = DEBUG
            for line in file_content.readlines():
                if not line.startswith("--"):
                    if "#newmonster" in line:
                        new_nation, new_monster = False, True
                        nation_id, nation_name, nation_era = "", "", ""
                        monster_id = re.findall(r"\d+", line)[0]
                    elif "#selectnation" in line:
                        new_nation, new_monster = True, False
                        monster_id, monster_name = "", ""
                        nation_id = re.findall(r"\d+", line)[0]
                    elif "#end" in line:
                        if new_monster and monster_name:
                            unit = Dom6Unit(
                                dominions_id=monster_id,
                                name=monster_name,
                                mod=mod,
                            )
                            unit.save(pipeline=pipeline)
                        elif new_nation and nation_name:
                            nation = Dom6Nation(
                                dominions_id=nation_id,
                                name=nation_name,
                                era=nation_era,
                                mod=mod,
                            )
                            nation.save(pipeline=pipeline)
                        new_nation, new_monster = False, False
                        monster_id, monster_name = "", ""
                        nation_id, nation_name, nation_era = "", "", ""
                    if new_monster or new_nation:
                        if "#name" in line and "nametype" not in line:
                            name = (
                                " ".join(line.split(" ")[1:])
                                .replace('"', "")
                                .strip()
                                .replace("\n", "")
                            )
                            if new_monster:
                                monster_name = name
                            elif new_nation:
                                nation_name = name
                        elif new_nation and "#era" in line:
                            nation_era = (
                                " ".join(line.split(" ")[1:])
                                .replace('"', "")
                                .replace("\n", "")
                            )
    pipeline.execute()
    pipeline.reset()


def parse_dom6_inventory():
    client = get_redis_client()
    pipeline = client.pipeline()
    item_pks = Dom6Item.all_pks()
    [Dom6Item.delete(item_pk, pipeline=pipeline) for item_pk in item_pks]
    pipeline.execute()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/BaseI.csv"), "r", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            item = Dom6Item(name=row["name"])
            item.save(pipeline=pipeline)
    pipeline.execute()
    pipeline.reset()
