import csv
import glob
import os
import re

from apps.core.consts import DEBUG
from apps.core.redis import get_redis_client
from apps.dom6data.autocalc import get_random_paths
from apps.dom6data.models import Dom6Item, Dom6Nation, Dom6Unit


def parse_dom6_units():
    """
    Parses the Dominions 6 units data, including nations, units, and leader types.

    This function reads data from CSV files, deletes existing records in Redis,
    and inserts new records based on the parsed data.
    """
    client = get_redis_client()
    pipeline = client.pipeline()

    # Delete existing unit records
    unit_ids = Dom6Unit.all_pks()
    [Dom6Unit.delete(unit_id, pipeline=pipeline) for unit_id in unit_ids]
    pipeline.execute()

    # Delete existing nation records
    nation_ids = Dom6Nation.all_pks()
    [Dom6Nation.delete(nation_id, pipeline=pipeline) for nation_id in nation_ids]
    pipeline.execute()

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Parse nations data from CSV file
    with open(
        os.path.join(current_dir, "csvs/nations.csv"), "r", newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            # Skip internal or not functional nations
            if row["era"] == "0":
                continue
            nation = Dom6Nation(
                name=row["name"], dominions_id=row["id"], era=row["era"]
            )
            nation.save(pipeline=pipeline)
    pipeline.execute()

    # Parse units data from CSV file
    row_to_data = []
    with open(os.path.join(current_dir, "csvs/BaseU.csv"), "r", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            unit = Dom6Unit(
                name=row["name"],
                dominions_id=row["id"],
                is_commander=False,
                holycost=row["holycost"] or None,
            )
            unit.save(pipeline=pipeline)
            to_append_dict = {
                "leader": row["leader"] or 0,
                "inspirational": row["inspirational"] or 0,
                "sailingshipsize": row["sailingshipsize"] or 0,
                "randompaths": get_random_paths(row),
            }
            for x in ["F", "A", "W", "E", "S", "D", "N", "G", "B"]:
                to_append_dict[x] = row[x] or 0
            row_to_data.append(to_append_dict)
    pipeline.execute()

    # Parse leader types data from CSV files
    leader_types_files = [
        "csvs/coast_leader_types_by_nation.csv",
        "csvs/fort_leader_types_by_nation.csv",
        "csvs/nonfort_leader_types_by_nation.csv",
    ]
    for filename in leader_types_files:
        with open(os.path.join(current_dir, filename), "r", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter="\t")
            for row in reader:
                nation = None
                try:
                    nations = Dom6Nation.find(
                        Dom6Nation.dominions_id == int(row["nation_number"])
                    ).all()
                    nation = nations[0]
                except IndexError:
                    print(f"Could not find nation with id {row['nation_number']}")
                try:
                    units = Dom6Unit.find(
                        (Dom6Unit.dominions_id == int(row["monster_number"]))
                    ).all()
                    unit = units[0]
                    unit.is_commander = True
                    if nation is not None:
                        unit.nations_ids.append(nation.pk)
                    unit.save(pipeline=pipeline)
                except IndexError:
                    print(f"Could not find unit with id {row['monster_number']}")
                    continue
    pipeline.execute()
    special_troop_file = "csvs/attributes_by_nation.csv"
    # some magic numbers, that I've gotten from searching source of the modinspector
    # https://github.com/larzm42/dom6inspector/blob/18abe8655a996148bd3baec69527a8c8e813f3e0/scripts/DMI/MNation.js#L87
    commander_attributes_numbers = [
        139,
        140,
        141,
        142,
        143,
        144,
        145,
        146,
        149,
        158,
        159,
        163,
        186,
        295,
        297,
        299,
        301,
        303,
        405,
        407,
        409,
        413,
        417,
        689,
        739,
    ]
    with open(
        os.path.join(current_dir, special_troop_file), "r", newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file, delimiter="\t")
        for row in reader:
            nation = None
            try:
                nations = Dom6Nation.find(
                    Dom6Nation.dominions_id == int(row["nation_number"])
                ).all()
                nation = nations[0]
            except IndexError:
                print(f"Could not find nation with id {row['nation_number']}")
                continue
            try:
                if int(row["attribute"]) not in commander_attributes_numbers:
                    continue
                units = Dom6Unit.find(
                    (Dom6Unit.dominions_id == int(row["raw_value"]))
                ).all()
                unit = units[0]
                unit.is_commander = True
                if nation is not None:
                    unit.nations_ids.append(nation.pk)
                unit.save(pipeline=pipeline)
            except IndexError:
                print(f"Could not find unit with id {row['raw_value']}")
                continue
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
                                is_commander=False,
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


if __name__ == "__main__":
    parse_dom6_units()
