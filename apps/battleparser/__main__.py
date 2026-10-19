"""CLI: python -m apps.battleparser screenshot.png [...] > result.json"""

import json
import sys

from apps.battleparser.parser import parse_battle_image


def main(paths):
    merged = {"nations": {}, "warnings": []}
    for path in paths:
        with open(path, "rb") as f:
            result = parse_battle_image(f.read())
        for nation, units in result.nations.items():
            merged["nations"].setdefault(nation, {}).update(units)
        merged["warnings"].extend(f"{path}: {w}" for w in result.warnings)
    json.dump(merged, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python -m apps.battleparser IMAGE [IMAGE ...]")
    main(sys.argv[1:])
