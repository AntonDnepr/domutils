# returned_data = process_data(serializer.validated_data)
# mapgenerated_text = data_into_map(returned_data)
# final_map = substitute(mapgenerated_text)


from string import Template

from core.consts import ERAS, LAND_STARTS, WATER_STARTS
from domdata.models import Nation


def process_data(data):
    nations_list = [
        data["land_nation_1"],
        data["land_nation_2"],
        data["water_nation_1"],
        data["water_nation_2"],
    ]
    returned_data = []
    for index, nation in enumerate(nations_list):
        if not bool(nation):
            continue
        units = [x for x in data["units"] if x["for_nation"] == nation]
        commanders = [x for x in data["commanders"] if x["for_nation"] == nation]
        age, nation_name = nation.split(")")
        age = age[1:]
        nation_name = nation_name.strip()
        dominions_id = [
            x
            for x in Nation.find(Nation.name == nation_name).all()
            if x.era == ERAS[age]
        ][0].dominions_id
        land_type = "land" if index < 2 else "water"
        nation_dict = {dominions_id: [], "land_type": land_type}
        for commander in commanders:
            magic = commander.get("magic")
            commander_data = {"units": []}
            if magic:
                commander_data["magic"] = {}
                for key, value in magic.items():
                    if value:
                        commander_data["magic"][f"mag_{key.lower()}"] = value
            nation_dict[dominions_id].append(
                {commander["dominions_id"]: commander_data}
            )
        commander_index, max_index = 0, len(commanders) - 1
        for index, unit in enumerate(units, start=0):
            if index % 3 == 0 and commander_index != max_index:
                commander_index += 1
            commander_to_append = nation_dict[dominions_id][commander_index]
            commander_id = list(commander_to_append)[0]
            commander_to_append[commander_id]["units"].append(
                (unit["dominions_id"], unit["quantity"])
            )
        returned_data.append(nation_dict)
    return returned_data


def data_into_map(data):
    order_to_map_position = {
        "land": [LAND_STARTS[0], LAND_STARTS[1]],
        "water": [WATER_STARTS[0], WATER_STARTS[1]],
    }
    returned_data = []
    for index, nation_data in enumerate(data):
        nation_id = list(nation_data.keys())[0]
        land_type = nation_data["land_type"]
        final_index = index
        if land_type == "water":
            # This works even for only water and land + water combos, because
            # python lists are supporting negative indexes
            final_index -= 2
        position_on_map = order_to_map_position[land_type][final_index]
        f_string = "\n#allowedplayer {0}\n#specstart {0} {1}\n#setland {1}".format(
            nation_id, position_on_map
        )
        for commander in nation_data[nation_id]:
            for commander_id, commander_data in commander.items():
                commander_string = "\n#commander {0}".format(commander_id)
                for units_data in commander_data.get("units", []):
                    unit_id, amount = units_data
                    commander_string += "\n#units {0} {1}".format(amount, unit_id)
                magic = commander_data.get("magic")
                if magic:
                    magic_string = "\n#clearmagic"
                    for key, value in magic.items():
                        magic_string += "\n#{0} {1}".format(key, value)
                    commander_string += magic_string
                f_string += commander_string
        returned_data.append(f_string)
    return returned_data


def substitute(data, mapgenerated_text, use_cave_map=False):
    data_dict = {f"nation{x}": y for x, y in enumerate(mapgenerated_text, start=1)}
    required_keys = [f"nation{x}" for x in range(1, 5)]
    for key in required_keys:
        if key not in data_dict:
            data_dict[key] = ""
    map_name = "Arena_with_cave" if use_cave_map else "Arena"
    with open(f"apps/domdata/mapfiles/{map_name}.map", "r") as mapfile:
        nations_list = [
            data.get("land_nation_1"),
            data.get("land_nation_2"),
            data.get("water_nation_1"),
            data.get("water_nation_2"),
        ]
        add_string, index = "", 0
        for nation in nations_list:
            if nation:
                if not index:
                    add_string += nation
                    index += 1
                else:
                    add_string += " vs {}".format(nation)
        final_map_name = f"{map_name}_{add_string}"
        data_dict["map_name"] = final_map_name
        src = Template(mapfile.read())
        result = src.substitute(data_dict)
    return result
