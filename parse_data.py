import sys

from apps.domdata.parser import parse_dm_files, parse_units

if __name__ == "__main__":
    sys.stdout.write("Start parsing \n")
    parse_units()
    parse_dm_files()
    sys.stdout.write("Parsing finished \n")
