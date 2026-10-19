"""Turn a battle report screenshot into
``{nation: {unit: {"quantity": int, "killed": int|None, "dead": int|None}}}``.
"""

import difflib
import os
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import cv2
import numpy as np
from apps.battleparser import digits
from apps.battleparser import layout as lay
from apps.battleparser import ocr

FORCES_PREFIX = "forces of "
PROVINCE_DEFENCE_PREFIX = "province defence"
NAME_MATCH_CUTOFF = 0.85
NATIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nations.txt")


def bundled_nation_names() -> List[str]:
    """Dominions 6 nation names (from dom6inspector's nations.csv)."""
    with open(NATIONS_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _fold(text: str) -> str:
    """Lowercase and strip accents, so OCR's "Pyréne" can match "Pyrène"."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


@dataclass
class ParseResult:
    nations: Dict[str, Dict[str, dict]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def _plural_variants(name: str) -> List[str]:
    variants = [name, name + "s", name + "es"]
    if name.endswith("y"):
        variants.append(name[:-1] + "ies")
    if name.endswith("man"):
        variants.append(name[:-3] + "men")
    return variants


class NameMatcher:
    """Snap OCR output to the closest known name, if one is close enough."""

    def __init__(self, names: Optional[Iterable[str]], plurals: bool = False):
        self.lookup: Dict[str, str] = {}
        for name in names or ():
            variants = _plural_variants(name) if plurals else [name]
            for variant in variants:
                self.lookup.setdefault(_fold(variant), variant)

    def __call__(self, text: str) -> str:
        key = _fold(text)
        if not self.lookup or key in self.lookup:
            return self.lookup.get(key, text)
        match = difflib.get_close_matches(
            key, self.lookup.keys(), n=1, cutoff=NAME_MATCH_CUTOFF
        )
        return self.lookup[match[0]] if match else text


def _clean_components(binary: np.ndarray, row_height: int) -> np.ndarray:
    """Drop specks of bright background texture."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary.astype(np.uint8), connectivity=8
    )
    min_area = max(4, int(12 * (row_height / 52) ** 2))
    keep = np.zeros(count, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[labels]


def _row_binary(image: np.ndarray, row: lay.Row, text_left: int) -> np.ndarray:
    strip = image[row.y0 : row.y1, text_left:].copy()
    height = row.y1 - row.y0
    margin = max(2, height // 12)
    for icon in row.icons:
        x0 = max(0, icon.x0 - text_left - margin)
        x1 = icon.x1 - text_left + margin
        strip[:, x0:x1] = 0
    gray = strip.max(axis=2)
    top = float(np.percentile(gray, 99.5))
    threshold = max(85.0, min(125.0, top * 0.6))
    return _clean_components(gray > threshold, height)


def _header_binary(image: np.ndarray, row: lay.Row, text_left: int) -> np.ndarray:
    band = image[row.y0 : row.y1, text_left:]
    hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    binary = (hsv[..., 1] < 90) & (hsv[..., 2] > 140)
    return _clean_components(binary, row.y1 - row.y0)


def row_cells(image, row: lay.Row, text_left: int):
    """Cut a table row into the name cell and number cells.

    Returns ``(name_binary, [(column, number_binary), ...])`` where column is
    "quantity", "killed" or "dead", or None if the row is empty.
    """
    height = row.y1 - row.y0
    binary = _row_binary(image, row, text_left)
    segments = lay.split_segments(binary, min_gap=max(8, int(height * 0.55)))
    if not segments:
        return None
    first = segments[0]
    numbers = []
    for segment in segments[1:]:
        x0 = segment.x0 + text_left
        # The icon right before a number tells which column it belongs to.
        icon = None
        for candidate in row.icons:
            if candidate.x1 <= x0 + 2 and x0 - candidate.x1 < height * 1.5:
                icon = candidate
        if icon is None:
            column = "quantity"
        elif icon.kind == "sword":
            column = "killed"
        else:
            column = "dead"
        numbers.append((column, binary[:, segment.x0 : segment.x1]))
    return binary[:, first.x0 : first.x1], numbers


def _read_row(image, row: lay.Row, text_left: int):
    """Return (name, {column: value}, raw_numbers) for one table row."""
    cells = row_cells(image, row, text_left)
    if cells is None:
        return None
    name_binary, numbers = cells
    name = ocr.read_text(name_binary, row.y1 - row.y0)
    values: Dict[str, int] = {}
    raw = []
    for column, binary in numbers:
        text = digits.read_number_text(binary)
        raw.append(text)
        value = digits.parse_number(text)
        if value is not None and column not in values:
            values[column] = value
    return name, values, raw


def _is_total(name: str) -> bool:
    return difflib.SequenceMatcher(None, name.lower(), "total").ratio() >= 0.75


def _nation_from_title(title: str) -> Optional[str]:
    lowered = title.lower()
    if lowered.startswith(FORCES_PREFIX):
        return title[len(FORCES_PREFIX) :].strip()
    # OCR may slightly garble the prefix; compare the first two words.
    words = title.split()
    if len(words) >= 3:
        prefix = " ".join(words[:2]).lower() + " "
        if difflib.SequenceMatcher(None, prefix, FORCES_PREFIX).ratio() >= 0.8:
            return " ".join(words[2:])
    return None


def parse_image(
    image: np.ndarray,
    unit_names: Optional[Iterable[str]] = None,
    nation_names: Optional[Iterable[str]] = None,
) -> ParseResult:
    match_unit = NameMatcher(unit_names, plurals=True)
    if nation_names is None:
        nation_names = bundled_nation_names()
    match_nation = NameMatcher(nation_names)
    result = ParseResult()
    layout = lay.analyse(image)
    image = layout.image

    nation: Optional[str] = None
    skipping = True  # until the first header we don't know whose rows these are
    block_sum = 0
    seen_header = False
    orphan_rows = 0

    for row in layout.rows:
        if row.is_header:
            seen_header = True
            title = ocr.read_text(
                _header_binary(image, row, layout.text_left), row.y1 - row.y0
            )
            block_sum = 0
            if title.lower().startswith(PROVINCE_DEFENCE_PREFIX):
                nation, skipping = None, True
                continue
            parsed = _nation_from_title(title)
            if parsed is None:
                result.warnings.append(f"Unrecognised block title: {title!r}")
                nation, skipping = None, True
                continue
            nation, skipping = match_nation(parsed), False
            result.nations.setdefault(nation, {})
            continue

        read = _read_row(image, row, layout.text_left)
        if read is None:
            continue
        name, values, raw = read
        quantity = values.get("quantity")

        if _is_total(name):
            if not skipping and nation is not None and quantity is not None:
                if quantity != block_sum:
                    result.warnings.append(
                        f"{nation}: unit quantities add up to {block_sum}, "
                        f"but the Total row says {quantity}"
                    )
            nation, skipping = None, True
            continue
        if skipping:
            if not seen_header:
                orphan_rows += 1
            continue
        if quantity is None:
            result.warnings.append(
                f"{nation}: could not read quantity for {name!r} (read {raw!r})"
            )
            continue
        unit = match_unit(name)
        result.nations[nation][unit] = {
            "quantity": quantity,
            "killed": values.get("killed"),
            "dead": values.get("dead"),
        }
        block_sum += quantity

    if orphan_rows:
        result.warnings.append(
            f"Skipped {orphan_rows} row(s) above the first block header"
        )
    return result


def parse_battle_image(
    data: bytes,
    unit_names: Optional[Iterable[str]] = None,
    nation_names: Optional[Iterable[str]] = None,
) -> ParseResult:
    return parse_image(lay.decode_image(data), unit_names, nation_names)
