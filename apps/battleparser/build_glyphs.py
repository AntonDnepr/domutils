"""Rebuild digit glyph templates from the labelled test screenshots.

    python -m apps.battleparser.build_glyphs

Each fixture ``tests/fixtures/X.webp`` (or .png) has ``X.json`` with the expected
units of each block. Number cells are cut out exactly like the parser does, labelled
with the expected value, and the averaged glyphs are saved to templates/glyphs/.
"""

import glob
import json
import os
from collections import defaultdict

import cv2
import numpy as np
from apps.battleparser import digits
from apps.battleparser import layout as lay
from apps.battleparser.parser import row_cells

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixtures")
# Cells whose printed text is not just str(value): "x+y" dead counts.
PRINTED_OVERRIDES = {
    ("sauromatia", "Witch Kings", "dead"): "0+3",
    ("sauromatia2", "Witch Kings", "dead"): "0+2",
    ("sauromatia2", "Androphag", "dead"): "0+1",
    ("sauromatia2", "Oiorpatas", "dead"): "37+13",
    ("sauromatia2", "Raiders", "dead"): "17+9",
    ("sauromatia2", "Sauromatian Cataphracts", "dead"): "26+7",
    ("sauromatia2", "Sauromatian Lancers", "dead"): "38+10",
}
FILE_NAMES = {"+": "plus", "-": "minus"}
# Glyphs from tiny text are too blurry to improve the templates.
MIN_LINE_HEIGHT = 20


def fixture_paths():
    for path in sorted(glob.glob(os.path.join(FIXTURES, "*"))):
        if os.path.splitext(path)[1] in (".webp", ".png"):
            yield path


def labelled_cells():
    """Yield (fixture, unit, column, printed_text, binary_cell).

    The nations in X.json must be in the order their blocks appear; blocks
    after the last listed nation (e.g. Province Defence) are ignored."""
    for path in fixture_paths():
        key = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(FIXTURES, key + ".json"), encoding="utf-8") as f:
            expected = json.load(f)
        layout = lay.analyse(cv2.imread(path))
        blocks = []
        for row in layout.rows:
            if row.is_header:
                blocks.append([])
            elif blocks:
                blocks[-1].append(row)
        for units, rows in zip(expected.values(), blocks):
            total = sum(values["quantity"] for values in units.values())
            labelled = list(units.items()) + [("Total", {"quantity": total})]
            for row, (unit, values) in zip(rows, labelled):
                cells = row_cells(layout.image, row, layout.text_left)
                for column, binary in cells[1] if cells else []:
                    text = PRINTED_OVERRIDES.get((key, unit, column))
                    if text is None and values.get(column) is not None:
                        text = str(values[column])
                    if text:
                        yield key, unit, column, text, binary


def main():
    samples = defaultdict(list)
    for key, unit, column, text, binary in labelled_cells():
        glyphs, line_height = digits.cut_glyphs(binary)
        if line_height < MIN_LINE_HEIGHT:
            continue
        if len(glyphs) != len(text):
            print(f"skip {key}/{unit}/{column}: {len(glyphs)} blobs for {text!r}")
            continue
        for char, glyph in zip(text, glyphs):
            samples[char].append(digits.normalise(glyph, line_height))
    os.makedirs(digits.GLYPH_DIR, exist_ok=True)
    for char, items in sorted(samples.items()):
        mean = np.mean(items, axis=0)
        name = FILE_NAMES.get(char, char)
        cv2.imwrite(
            os.path.join(digits.GLYPH_DIR, f"{name}.png"),
            np.clip(mean * 255, 0, 255).astype(np.uint8),
        )
        print(f"{char!r}: {len(items)} samples")


if __name__ == "__main__":
    main()
