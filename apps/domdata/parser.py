import csv
import glob
import os
import re

from apps.core.consts import DE, DEBUG
from apps.core.redis import get_redis_client
from apps.domdata.models import Nation, Unit


def parse_units():
    client = get_redis_client()
    pipeline = client.pipeline()
    unit_ids = Unit.all_pks()
    [Unit.delete(unit_id, pipeline=pipeline) for unit_id in unit_ids]
    pipeline.execute()
    nation_ids = Nation.all_pks()
    [Nation.delete(nation_id, pipeline=pipeline) for nation_id in nation_ids]
    pipeline.execute()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "csvs/BaseU.csv"), "r", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            unit = Unit(name=row["name"], dominions_id=row["id"])
            unit.save(pipeline=pipeline)
    pipeline.execute()

    with open(
        os.path.join(current_dir, "csvs/nations.csv"), "r", newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            nation = Nation(name=row["name"], dominions_id=row["id"], era=row["era"])
            nation.save(pipeline=pipeline)
    pipeline.execute()
    pipeline.reset()


def parse_dm_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_parse = glob.glob(os.path.join(current_dir, "mods/*.dm"))
    pipeline = get_redis_client().pipeline()
    try:
        units = Unit.find((Unit.mod == DEBUG) | (Unit.mod == DE)).all()
        [Unit.delete(unit.pk, pipeline=pipeline) for unit in units]
        pipeline.execute()
        nations = Nation.find((Nation.mod == DEBUG) | (Nation.mod == DE))
        [Nation.delete(nation.pk, pipeline=pipeline) for nation in nations]
        pipeline.execute()
    except Exception as e:
        print(e)
        pass
    for dmfile in files_to_parse:
        with open(dmfile, "r") as file_content:
            new_nation, new_monster = False, False
            monster_id, monster_name = "", ""
            nation_id, nation_name, nation_era = "", "", ""
            mod = DE if "DomEnhanced" in dmfile else DEBUG
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
                            unit = Unit(
                                dominions_id=monster_id,
                                name=monster_name,
                                mod=mod,
                            )
                            unit.save(pipeline=pipeline)
                        elif new_nation and nation_name:
                            nation = Nation(
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
