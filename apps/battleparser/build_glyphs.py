"""Rebuild digit glyph templates from the labelled test screenshots.

    python -m apps.battleparser.build_glyphs

Each fixture ``tests/fixtures/X.webp`` has ``X.json`` with the expected units of
its first block. Number cells are cut out exactly like the parser does, labelled
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
# Cells whose printed text is not just str(value).
PRINTED_OVERRIDES = {("sauromatia", "Witch Kings", "dead"): "0+3"}
FILE_NAMES = {"+": "plus", "-": "minus"}


def labelled_cells():
    for path in sorted(glob.glob(os.path.join(FIXTURES, "*.webp"))):
        key = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(FIXTURES, key + ".json"), encoding="utf-8") as f:
            units = list(next(iter(json.load(f).values())).items())
        layout = lay.analyse(cv2.imread(path))
        rows = []
        started = False
        for row in layout.rows:
            if row.is_header:
                if started:
                    break
                started = True
                continue
            if started:
                rows.append(row)
        total = sum(values["quantity"] for _, values in units)
        expected = units + [("Total", {"quantity": total})]
        for row, (unit, values) in zip(rows, expected):
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
