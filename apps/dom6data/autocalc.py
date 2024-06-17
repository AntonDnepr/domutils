# based on dominspector
def autocalc(data_dict):
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
            data_dict.get(x, "0") for x in ["F", "A", "W", "E", "S", "D", "N", "G", "B"]
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
                        temp_path_cost = path1[arr[rand2][rand3]]
                    else:
                        temp_path_cost += path2[arr[rand2][rand3]]
                if largest == 0:
                    largest = temp_path_cost
                    smallest = temp_path_cost
                else:
                    if temp_path_cost > largest:
                        largest = temp_path_cost
                    elif temp_path_cost < smallest:
                        smallest = temp_path_cost
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
        if "inept_research" in data_dict:
            paths_cost -= 5
        if "fixforgebonus" in data_dict:
            paths_cost += paths_cost * (int(data_dict["fixforgebonus"]) / 100)

        priest = {1: 20, 2: 40, 3: 100, 4: 140}
        priest_cost = 0
        if "H" in data_dict:
            priest_cost = priest.get(int(data_dict["H"]), 0)

        spy_cost = 0
        if "spy" in data_dict and int(data_dict["spy"]) > 0:
            spy_cost += 40
        if "assassin" in data_dict and int(data_dict["assassin"]) > 0:
            spy_cost += 40
        if "seduce" in data_dict and int(data_dict["seduce"]) > 0:
            spy_cost += 60
        elif "succubus" in data_dict and int(data_dict["succubus"]) > 0:
            spy_cost += 60

        cost_array = [ldr_cost, paths_cost, priest_cost, spy_cost]
        cost_array.sort(reverse=True)

        cost = 0
        if "type" in data_dict and data_dict["type"] == "c":
            cost = (
                cost_array[0]
                + cost_array[1] / 2
                + cost_array[2] / 2
                + cost_array[3] / 2
            )
        else:
            cost = 0

        special_cost = 0
        if (
            "stealthy" in data_dict
            and int(data_dict["stealthy"]) > 0
            and "type" in data_dict
            and data_dict["type"] != "u"
        ):
            special_cost += 5
        if (
            "autohealer" in data_dict
            and int(data_dict["autohealer"]) > 0
            and "type" in data_dict
            and data_dict["type"] != "u"
        ):
            special_cost += 50
        if (
            "autodishealer" in data_dict
            and int(data_dict["autodishealer"]) > 0
            and "type" in data_dict
            and data_dict["type"] != "u"
        ):
            special_cost += 20

        goldcost = int(cost + special_cost)
        goldcost += int(data_dict["basecost"]) - 10000
        if (
            "slow_to_recruit" in data_dict
            and int(data_dict["slow_to_recruit"]) > 0
            and "type" in data_dict
            and data_dict["type"] != "u"
        ):
            goldcost = int(goldcost * 0.9)
        if "holy" in data_dict and int(data_dict["holy"]) > 0:
            goldcost = int(goldcost * 1.3)
        if "type" in data_dict and data_dict["type"] == "u":
            goldcost = round_if_needed(goldcost)
        else:
            if "mountmnr" in data_dict:
                goldcost = special_round(goldcost * 1.4)
                goldcost = round_up(goldcost * 1.01)
            else:
                goldcost = special_round(goldcost * 1.4)
    else:
        goldcost = round_if_needed(data_dict["basecost"])
    return goldcost or 0


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


def build_random_arrays(o, i, arr, base_magic):
    r = o["randompaths"][i]
    if "chance" in r and int(r["chance"]) != 100:
        i += 1
        if i == len(o["randompaths"]):
            return False
        r = o["randompaths"][i]
        if "chance" in r and int(r["chance"]) != 100:
            i += 1
            if i == len(o["randompaths"]):
                return False
            r = o["randompaths"][i]
            if "chance" in r and int(r["chance"]) != 100:
                i += 1
                if i == len(o["randompaths"]):
                    return False
                r = o["randompaths"][i]
            if "chance" in r and int(r["chance"]) != 100:
                i += 1
                if i == len(o["randompaths"]):
                    return False
                r = o["randompaths"][i]
    if "chance" in r and int(r["chance"]) == 100:
        new_magic = base_magic.copy()
        for step in r["paths"]:
            if step == "F":
                if new_magic[0]:
                    new_magic[0] = int(new_magic[0]) + int(r["levels"])
                else:
                    new_magic[0] = int(r["levels"])
            elif step == "A":
                if new_magic[1]:
                    new_magic[1] = int(new_magic[1]) + int(r["levels"])
                else:
                    new_magic[1] = int(r["levels"])
            elif step == "W":
                if new_magic[2]:
                    new_magic[2] = int(new_magic[2]) + int(r["levels"])
                else:
                    new_magic[2] = int(r["levels"])
            elif step == "E":
                if new_magic[3]:
                    new_magic[3] = int(new_magic[3]) + int(r["levels"])
                else:
                    new_magic[3] = int(r["levels"])
            elif step == "S":
                if new_magic[4]:
                    new_magic[4] = int(new_magic[4]) + int(r["levels"])
                else:
                    new_magic[4] = int(r["levels"])
            elif step == "D":
                if new_magic[5]:
                    new_magic[5] = int(new_magic[5]) + int(r["levels"])
                else:
                    new_magic[5] = int(r["levels"])
            elif step == "N":
                if new_magic[6]:
                    new_magic[6] = int(new_magic[6]) + int(r["levels"])
                else:
                    new_magic[6] = int(r["levels"])
            elif step == "G":
                if new_magic[7]:
                    new_magic[7] = int(new_magic[7]) + int(r["levels"])
                else:
                    new_magic[7] = int(r["levels"])
            elif step == "B":
                if new_magic[8]:
                    new_magic[8] = int(new_magic[8]) + int(r["levels"])
                else:
                    new_magic[8] = int(r["levels"])
        if i + 1 < len(o["randompaths"]):
            i += 1
            if not build_random_arrays(o, i, arr, new_magic):
                arr.append(new_magic)
            i -= 1
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
        level_value = row[level_key] or None
        chance_value = row[chance_key] or None
        pstr = ""
        for k in pmasks.keys():
            if bit_value & int(k):
                pstr += pmasks[k]
        for j in range(repeat_value):
            randompaths.append(
                {"paths": pstr, "levels": level_value, "chance": chance_value}
            )
    return randompaths
