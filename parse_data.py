import sys

from apps.dom6data.loader import load_required_data
from apps.dom6data.parser import parse_dom6_units, parse_dom6_dm_files
from apps.domdata.parser import parse_dm_files, parse_units

if __name__ == "__main__":
    sys.stdout.write("Start parsing \n")
    parse_units()
    parse_dm_files()
    load_required_data()
    parse_dom6_units()
    parse_dom6_dm_files()
    sys.stdout.write("Parsing finished \n")
