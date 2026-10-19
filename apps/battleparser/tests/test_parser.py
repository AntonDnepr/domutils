import glob
import json
import os

import pytest
from apps.battleparser.digits import parse_number
from apps.battleparser.parser import NameMatcher, parse_battle_image

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
IMAGES = sorted(
    p for p in glob.glob(os.path.join(FIXTURES, "*")) if p.endswith((".webp", ".png"))
)


@pytest.mark.parametrize("path", IMAGES, ids=os.path.basename)
def test_parse_fixture(path):
    with open(path, "rb") as f:
        result = parse_battle_image(f.read())
    with open(os.path.splitext(path)[0] + ".json", encoding="utf-8") as f:
        expected = json.load(f)
    assert result.nations == expected
    assert result.warnings == []


@pytest.mark.parametrize(
    "text, value",
    [("12", 12), ("-1", -1), ("0+3", 3), ("", None), ("1?", None)],
)
def test_parse_number(text, value):
    assert parse_number(text) == value


def test_name_matcher_snaps_plurals_and_typos():
    match = NameMatcher(["Sidhe Lord", "Clockwork Horror"], plurals=True)
    assert match("Sidhe Lords") == "Sidhe Lords"
    assert match("Clockwork Horrars") == "Clockwork Horrors"
    assert match("Something Else") == "Something Else"


def test_name_matcher_pluralises_before_of():
    match = NameMatcher(["Equite of the Sacred Shroud"], plurals=True)
    assert match("Equites of the Sacred Shroud") == "Equites of the Sacred Shroud"


def test_name_matcher_without_names_is_identity():
    assert NameMatcher(None)("Pyréne") == "Pyréne"


def test_rows_above_first_header_are_skipped_with_warning():
    import cv2
    from apps.battleparser.parser import parse_image

    image = cv2.imread(os.path.join(FIXTURES, "tirnanog_pd.webp"))
    # Crop away the "Forces of" header; the rest is its tail + Province Defence.
    result = parse_image(image[300:])
    assert result.nations == {}
    assert result.warnings == ["Skipped 2 row(s) above the first block header"]
