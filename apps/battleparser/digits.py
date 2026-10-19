"""Read numbers by matching glyphs against templates of the game font (no OCR engine).

Numbers in the report only use ``0-9``, ``+`` and ``-``. Every glyph is a separate
connected blob, so each blob is cut out, scaled to a fixed height (keeping its
width) and compared with the stored template of every character.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

GLYPH_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates", "glyphs"
)
GLYPH_HEIGHT = 36
GLYPH_WIDTH = 36
GLYPH_NAMES = {"plus": "+", "minus": "-"}
# A glyph whose best match is worse than this is reported as unreadable. Large
# text matches within ~0.12; tiny (~11px) text within ~0.37; junk blobs >= 0.45.
MAX_DISTANCE = 0.42


def components(binary: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Bounding boxes (x0, y0, x1, y1) of blobs, merged when they overlap in x."""
    count, _, stats, _ = cv2.connectedComponentsWithStats(
        binary.astype(np.uint8), connectivity=8
    )
    boxes = []
    for i in range(1, count):
        x, y, w, h, _ = stats[i]
        boxes.append([x, y, x + w, y + h])
    boxes.sort()
    merged: List[List[int]] = []
    for box in boxes:
        if merged and box[0] < merged[-1][2] - 1:
            last = merged[-1]
            merged[-1] = [
                min(last[0], box[0]),
                min(last[1], box[1]),
                max(last[2], box[2]),
                max(last[3], box[3]),
            ]
        else:
            merged.append(box)
    return [tuple(b) for b in merged]


def normalise(glyph: np.ndarray, line_height: int) -> np.ndarray:
    """Scale by the line height (not the glyph's own) so that small glyphs
    such as ``+`` and ``-`` keep their size information."""
    scale = GLYPH_HEIGHT / max(1, line_height)
    w = max(1, round(glyph.shape[1] * scale))
    h = max(1, round(glyph.shape[0] * scale))
    resized = cv2.resize(
        glyph.astype(np.float32),
        (min(w, GLYPH_WIDTH), min(h, GLYPH_HEIGHT)),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.zeros((GLYPH_HEIGHT, GLYPH_WIDTH), np.float32)
    y0 = (GLYPH_HEIGHT - resized.shape[0]) // 2
    x0 = (GLYPH_WIDTH - resized.shape[1]) // 2
    canvas[y0 : y0 + resized.shape[0], x0 : x0 + resized.shape[1]] = resized
    return canvas


def cut_glyphs(binary: np.ndarray) -> Tuple[List[np.ndarray], int]:
    """Return the blobs of a number cell, left to right, and the line height.

    Each blob keeps the full line height so that its vertical position is part
    of the shape ('-' sits mid-height, digits fill the line)."""
    boxes = components(binary)
    if not boxes:
        return [], 0
    rows = np.nonzero(binary.any(axis=1))[0]
    top, bottom = rows[0], rows[-1] + 1
    return [binary[top:bottom, x0:x1] for x0, _, x1, _ in boxes], bottom - top


_TEMPLATES: Optional[Dict[str, np.ndarray]] = None


def templates() -> Dict[str, np.ndarray]:
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = {}
        for filename in sorted(os.listdir(GLYPH_DIR)):
            name, ext = os.path.splitext(filename)
            if ext != ".png":
                continue
            image = cv2.imread(os.path.join(GLYPH_DIR, filename), cv2.IMREAD_GRAYSCALE)
            _TEMPLATES[GLYPH_NAMES.get(name, name)] = image.astype(np.float32) / 255
    return _TEMPLATES


def classify(normalised: np.ndarray) -> Tuple[str, float]:
    best_char, best_distance = "?", 1.0
    for char, template in templates().items():
        diff = np.abs(normalised - template).sum()
        distance = diff / max(1.0, normalised.sum() + template.sum())
        if distance < best_distance:
            best_char, best_distance = char, distance
    return best_char, best_distance


def read_number_text(binary: np.ndarray) -> str:
    glyphs, line_height = cut_glyphs(binary)
    chars = []
    for glyph in glyphs:
        char, distance = classify(normalise(glyph, line_height))
        chars.append(char if distance <= MAX_DISTANCE else "?")
    return "".join(chars)


_NUMBER_RE = re.compile(r"^(-?\d+)(?:\+(\d+))?$")


def parse_number(text: str) -> Optional[int]:
    """Parse a cell like ``12``, ``-1`` or ``0+3`` (summed to 3)."""
    match = _NUMBER_RE.match(text)
    if not match:
        return None
    value = int(match.group(1))
    if match.group(2):
        value += int(match.group(2))
    return value
