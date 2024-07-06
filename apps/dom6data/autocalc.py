# based on dominspector
import copy


def calc_gold_cost(data_dict):
    goldcost = None
    if int(data_dict["basecost"]) > 9000:
        leadership = {
            0: 10,
            10: 15,
            20: 20,
            30: 20,
            40: 30,
            50: 30,
            60: 30,
            75: 30,
            80: 60,
            100: 60,
            120: 80,
            150: 100,
            160: 100,
            200: 150,
        }

        ldr_cost = 0
        ldr_cost += leadership.get(int(data_dict["leader"]), 0)
        ldr_cost += 10 * int(data_dict["inspirational"])
        if int(data_dict["sailingshipsize"]) > 0:
            ldr_cost += 0.5 * ldr_cost

        path1 = {1: 30, 2: 90, 3: 150, 4: 210, 5: 270}
        path2 = {1: 20, 2: 60, 3: 100, 4: 140, 5: 180}

        paths_cost = 0
        arr = []
        base_magic = [
            int(data_dict.get(x, 0))
            for x in ["F", "A", "W", "E", "S", "D", "N", "G", "B"]
        ]
        if has_random(data_dict):
            build_random_arrays(data_dict, 0, arr, base_magic)
            for rand1 in range(len(arr)):
                arr[rand1].sort(reverse=True)
            largest = 0
            smallest = 0
            for rand2 in range(len(arr)):
                temp_path_cost = 0
                for rand3 in range(len(arr[rand2])):
                    if rand3 == 0:
                        temp_path_cost = path1.get(arr[rand2][rand3], 0)
                    else:
                        temp_path_cost += path2.get(arr[rand2][rand3], 0)
                if largest == 0:
                    largest = temp_path_cost
                    smallest = temp_path_cost
                else:
                    if temp_path_cost > largest:
                        largest = temp_path_cost
                    elif temp_path_cost < smallest:
                        smallest = temp_path_cost
            # largest should be 210, but it's 330 for some reason
            paths_cost = (largest * 0.75) + (smallest * 0.25)
        else:
            sorted_arr = []
            for oj in range(len(base_magic)):
                if int(base_magic[oj]) > 0:
                    sorted_arr.append(int(base_magic[oj]))
            sorted_arr.sort(reverse=True)
            for ok in range(len(sorted_arr)):
                if ok == 0:
                    paths_cost = path1[sorted_arr[ok]]
                else:
                    paths_cost += path2[sorted_arr[ok]]

        if paths_cost > 0 and "adept_research" in data_dict:
            paths_cost += int(data_dict["adept_research"]) * 5
        if int(data_dict["inept_research"]) != 0:
            paths_cost -= 5
        if int(data_dict["fixforgebonus"]) > 0:
            paths_cost += paths_cost * (int(data_dict["fixforgebonus"]) / 100)

        priest = {1: 20, 2: 40, 3: 100, 4: 140}
        priest_cost = 0
        if "H" in data_dict:
            priest_cost = priest.get(int(data_dict["H"]), 0)

        spy_cost = 0
        if int(data_dict["spy"]) > 0:
            spy_cost += 40
        if int(data_dict["assassin"]) > 0:
            spy_cost += 40
        if int(data_dict["seduce"]) > 0:
            spy_cost += 60
        elif int(data_dict["succubus"]) > 0:
            spy_cost += 60

        cost_array = [ldr_cost, paths_cost, priest_cost, spy_cost]
        cost_array.sort(reverse=True)
        cost = 0
        if data_dict["type"] == "commander":
            cost = (
                cost_array[0]
                + cost_array[1] / 2
                + cost_array[2] / 2
                + cost_array[3] / 2
            )

        special_cost = 0
        if data_dict["type"] == "commander":
            if int(data_dict["stealthy"]) > 0:
                special_cost += 5
            if int(data_dict["autohealer"]) > 0:
                special_cost += 50
            if int(data_dict["autodishealer"]) > 0:
                special_cost += 20
        goldcost = int(cost + special_cost)
        goldcost += int(data_dict["basecost"]) - 10000
        if int(data_dict["slow_to_recruit"]) > 0 and data_dict["type"] != "unit":
            goldcost = int(goldcost * 0.9)
        if int(data_dict["holy"]) > 0:
            goldcost = int(goldcost * 1.3)
        if data_dict["type"] == "unit":
            goldcost = round_if_needed(goldcost)
        else:
            if int(data_dict["mountmnr"]) != 0:
                goldcost = special_round(goldcost * 1.4)
                goldcost = round_up(goldcost * 1.01)
            else:
                goldcost = special_round(goldcost * 1.4)
    else:
        goldcost = round_if_needed(data_dict["basecost"])
    return max(goldcost or 0, 0)


def round_if_needed(num):
    num = float(num)
    if num > 30:
        return special_round(num)
    return int(num)


def special_round(num):
    num = float(num)
    return int(5 * (num // 5))


def round_up(num):
    num = float(num)
    if num % 5 == 0:
        return int(num)
    return int(5 * (num // 5 + 1))


def has_random(o):
    if len(o.get("randompaths", [])) > 0:
        for r in o["randompaths"]:
            if "chance" in r and int(r["chance"]) == 100:
                return True
    return False


def build_random_arrays(data_dict, index, arr, base_magic):
    randompath = data_dict["randompaths"][index]
    if int(randompath.get("chance", 0)) != 100:
        index += 1
        if index == len(data_dict["randompaths"]):
            return False
        randompath = data_dict["randompaths"][index]
        if int(randompath.get("chance", 0)) != 100:
            index += 1
            if index == len(data_dict["randompaths"]):
                return False
            randompath = data_dict["randompaths"][index]
            if int(randompath.get("chance", 0)) != 100:
                index += 1
                if index == len(data_dict["randompaths"]):
                    return False
                randompath = data_dict["randompaths"][index]
            if int(randompath.get("chance", 0)) != 100:
                index += 1
                if index == len(data_dict["randompaths"]):
                    return False
                randompath = data_dict["randompaths"][index]
    if int(randompath.get("chance", 0)) == 100:
        for step in randompath["paths"]:
            new_magic = copy.deepcopy(base_magic)
            if step == "F":
                if new_magic[0]:
                    new_magic[0] = int(new_magic[0]) + int(randompath["levels"])
                else:
                    new_magic[0] = int(randompath["levels"])
            elif step == "A":
                if new_magic[1]:
                    new_magic[1] = int(new_magic[1]) + int(randompath["levels"])
                else:
                    new_magic[1] = int(randompath["levels"])
            elif step == "W":
                if new_magic[2]:
                    new_magic[2] = int(new_magic[2]) + int(randompath["levels"])
                else:
                    new_magic[2] = int(randompath["levels"])
            elif step == "E":
                if new_magic[3]:
                    new_magic[3] = int(new_magic[3]) + int(randompath["levels"])
                else:
                    new_magic[3] = int(randompath["levels"])
            elif step == "S":
                if new_magic[4]:
                    new_magic[4] = int(new_magic[4]) + int(randompath["levels"])
                else:
                    new_magic[4] = int(randompath["levels"])
            elif step == "D":
                if new_magic[5]:
                    new_magic[5] = int(new_magic[5]) + int(randompath["levels"])
                else:
                    new_magic[5] = int(randompath["levels"])
            elif step == "N":
                if new_magic[6]:
                    new_magic[6] = int(new_magic[6]) + int(randompath["levels"])
                else:
                    new_magic[6] = int(randompath["levels"])
            elif step == "G":
                if new_magic[7]:
                    new_magic[7] = int(new_magic[7]) + int(randompath["levels"])
                else:
                    new_magic[7] = int(randompath["levels"])
            elif step == "B":
                if new_magic[8]:
                    new_magic[8] = int(new_magic[8]) + int(randompath["levels"])
                else:
                    new_magic[8] = int(randompath["levels"])
        if index + 1 < len(data_dict["randompaths"]):
            index += 1
            if not build_random_arrays(data_dict, index, arr, new_magic):
                arr.append(new_magic)
            index -= 1
        else:
            arr.append(new_magic)
    else:
        return False
    return True


def get_random_paths(row):
    valid_keys = [x for x in row.keys() if x.startswith("mask")]
    valid_numbers = [int(x.replace("mask", "")) for x in valid_keys]
    pmasks = {
        128: "F",
        256: "A",
        512: "W",
        1024: "E",
        2048: "S",
        4096: "D",
        8192: "N",
        16384: "G",
        32768: "B",
        65536: "H",
    }
    randompaths = []
    for valid_number in valid_numbers:
        mask_key = f"mask{valid_number}"
        level_key = f"link{valid_number}"
        chance_key = f"rand{valid_number}"
        repeat_value = int(row[f"nbr{valid_number}"] or 0)
        bit_value = int(row[mask_key] or 0)
        level_value = row[level_key] or 0
        chance_value = row[chance_key] or 0
        pstr = ""
        for k in pmasks.keys():
            if bit_value & int(k):
                pstr += pmasks[k]
        for j in range(repeat_value):
            randompaths.append(
                {"paths": pstr, "levels": int(level_value), "chance": chance_value}
            )
    return randompaths
