"""Geometry of a Dominions battle report screenshot, found with plain image processing.

The report is a table: a reddish header band ("Forces of X") followed by unit rows
(name | quantity | sword icon + killed | cross icon + dead) and a grey "Total" row.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
# Row pitch (in px) of the screenshot the icon templates were cut from.
TEMPLATE_ROW_PITCH = 59.5

# Brightness (max of B, G, R) above which a pixel counts as text.
TEXT_MIN_BRIGHTNESS = 110
ICON_MATCH_THRESHOLD = 0.6


@dataclass
class Icon:
    kind: str  # "sword" or "cross"
    x0: int
    x1: int


@dataclass
class Segment:
    """A horizontal run of text in a row (a name or a number)."""

    x0: int
    x1: int


@dataclass
class Row:
    y0: int
    y1: int
    is_header: bool = False
    icons: List[Icon] = field(default_factory=list)


@dataclass
class Layout:
    image: np.ndarray
    text_left: int
    rows: List[Row]


def decode_image(data: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")
    return image


def _runs(mask: np.ndarray) -> List[Tuple[int, int]]:
    """Return [start, end) index pairs of consecutive True values."""
    padded = np.concatenate(([False], mask, [False])).astype(np.int8)
    diff = np.diff(padded)
    starts = np.nonzero(diff == 1)[0]
    ends = np.nonzero(diff == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def header_mask(image: np.ndarray) -> np.ndarray:
    """Pixels with the solid reddish-brown colour of a block header band."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return ((hue <= 15) | (hue >= 170)) & (sat > 110) & (val > 65) & (val < 135)


def find_header_bands(image: np.ndarray) -> List[Tuple[int, int]]:
    width = image.shape[1]
    fraction = header_mask(image).sum(axis=1) / width
    # A long title covers part of the band, so accept rows with a lower
    # fraction as long as the band as a whole is wide.
    bands = _runs(fraction > 0.3)
    return [
        (y0, y1) for y0, y1 in bands if y1 - y0 >= 8 and fraction[y0:y1].max() > 0.5
    ]


def remove_vertical_lines(image: np.ndarray, top: int = 0) -> np.ndarray:
    """Blank bright vertical lines (window frames, scrollbars) below ``top``.

    Text columns are bright in at most about a third of the rows; a frame is
    bright almost everywhere."""
    region = text_mask(image[top:])
    if region.shape[0] == 0:
        return image
    lines = region.mean(axis=0) > 0.7
    if not lines.any():
        return image
    lines = cv2.dilate(lines.astype(np.uint8)[None, :], np.ones((1, 5), np.uint8))
    cleaned = image.copy()
    cleaned[:, lines[0].astype(bool)] = (25, 25, 25)
    return cleaned


def find_text_left(image: np.ndarray, headers: List[Tuple[int, int]]) -> int:
    """X where titles and unit names start (right of the unit portraits)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    width = image.shape[1]
    candidates = []
    for y0, y1 in headers:
        band = hsv[y0:y1]
        # Title text is light grey: low saturation, bright.
        text = (band[..., 1] < 70) & (band[..., 2] > 170)
        # The title is the widest run of text; the banner pole that overlaps
        # the band on the left is a separate narrow run.
        segments = split_segments(text, min_gap=max(4, (y1 - y0) // 2))
        segments = [s for s in segments if s.x0 > width * 0.02]
        if segments:
            title = max(segments, key=lambda s: s.x1 - s.x0)
            candidates.append(title.x0)
    if candidates:
        return max(0, min(candidates) - 6)
    return int(width * 0.075)


def text_mask(image: np.ndarray, threshold: int = TEXT_MIN_BRIGHTNESS) -> np.ndarray:
    return image.max(axis=2) > threshold


def find_text_rows(
    image: np.ndarray, text_left: int, headers: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    height = image.shape[0]
    mask = text_mask(image)[:, text_left:]
    # Grey "Total" rows are dimmer than unit rows but still above the threshold.
    counts = mask.sum(axis=1)
    is_text = counts >= 3
    for y0, y1 in headers:
        is_text[y0:y1] = False
    # Close tiny vertical gaps (e.g. between the dot and the stem of an "i").
    bands = _runs(is_text)
    merged: List[List[int]] = []
    for y0, y1 in bands:
        if merged and y0 - merged[-1][1] <= 3:
            merged[-1][1] = y1
        else:
            merged.append([y0, y1])
    if not merged:
        return []
    heights = sorted(y1 - y0 for y0, y1 in merged)
    typical = heights[len(heights) // 2]
    rows = []
    for y0, y1 in merged:
        if y1 - y0 < typical * 0.5:
            continue
        # A row cut off by the screenshot border cannot be read reliably.
        if y0 == 0 or y1 >= height:
            continue
        rows.append((y0, y1))
    return rows


_TEMPLATE_CACHE: dict = {}


def _template(kind: str) -> np.ndarray:
    if kind not in _TEMPLATE_CACHE:
        path = os.path.join(TEMPLATES_DIR, f"{kind}.png")
        _TEMPLATE_CACHE[kind] = cv2.imread(path, cv2.IMREAD_COLOR)
    return _TEMPLATE_CACHE[kind]


def find_icons(strip: np.ndarray, scale: float) -> List[Icon]:
    """Template-match sword and cross icons in one row strip."""
    icons: List[Icon] = []
    for kind in ("sword", "cross"):
        best: Optional[Tuple[float, int, int]] = None
        for factor in (0.85, 0.92, 1.0, 1.08, 1.16):
            template = _template(kind)
            size = (
                max(4, round(template.shape[1] * scale * factor)),
                max(4, round(template.shape[0] * scale * factor)),
            )
            resized = cv2.resize(template, size, interpolation=cv2.INTER_AREA)
            if resized.shape[0] > strip.shape[0] or resized.shape[1] > strip.shape[1]:
                continue
            result = cv2.matchTemplate(strip, resized, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(result)
            if best is None or score > best[0]:
                best = (score, loc[0], loc[0] + resized.shape[1])
        if best and best[0] >= ICON_MATCH_THRESHOLD:
            icons.append(Icon(kind, best[1], best[2]))
    return sorted(icons, key=lambda icon: icon.x0)


CURSOR_MATCH_THRESHOLD = 0.9


def remove_cursor(image: np.ndarray) -> np.ndarray:
    """Paint out the mouse pointer if the screenshot caught it over the table."""
    template = _template("cursor").max(axis=2)
    gray = image.max(axis=2)
    best = None
    for factor in (0.75, 1.0, 1.25, 1.5, 2.0):
        resized = cv2.resize(template, None, fx=factor, fy=factor)
        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(result)
        if best is None or score > best[0]:
            best = (score, loc, resized)
    if best is None or best[0] < CURSOR_MATCH_THRESHOLD:
        return image
    _, (x, y), resized = best
    body = cv2.dilate((resized > 120).astype(np.uint8), np.ones((3, 3), np.uint8))
    cleaned = image.copy()
    area = cleaned[y : y + body.shape[0], x : x + body.shape[1]]
    area[body.astype(bool)] = (25, 25, 25)
    return cleaned


def analyse(image: np.ndarray) -> Layout:
    image = remove_cursor(image)
    headers = find_header_bands(image)
    image = remove_vertical_lines(image, headers[0][0] if headers else 0)
    text_left = find_text_left(image, headers)
    text_rows = find_text_rows(image, text_left, headers)

    pitches = [b[0] - a[0] for a, b in zip(text_rows, text_rows[1:])]
    pitch = float(np.median(pitches)) if pitches else TEMPLATE_ROW_PITCH
    # Pitch between neighbouring unit rows; larger gaps span a header.
    if pitches:
        small = [p for p in pitches if p <= pitch * 1.3]
        pitch = float(np.median(small)) if small else pitch
    scale = pitch / TEMPLATE_ROW_PITCH

    rows = [Row(y0, y1, is_header=True) for y0, y1 in headers]
    pad = max(2, int(pitch * 0.12))
    for y0, y1 in text_rows:
        top, bottom = max(0, y0 - pad), min(image.shape[0], y1 + pad)
        strip = image[top:bottom, text_left:]
        icons = [
            Icon(icon.kind, icon.x0 + text_left, icon.x1 + text_left)
            for icon in find_icons(strip, scale)
        ]
        rows.append(Row(top, bottom, icons=icons))
    rows.sort(key=lambda row: row.y0)
    return Layout(image=image, text_left=text_left, rows=rows)


def split_segments(binary: np.ndarray, min_gap: int) -> List[Segment]:
    """Split a binarised row into text runs separated by at least ``min_gap`` px."""
    cols = binary.any(axis=0)
    runs = _runs(cols)
    segments: List[List[int]] = []
    for x0, x1 in runs:
        if segments and x0 - segments[-1][1] < min_gap:
            segments[-1][1] = x1
        else:
            segments.append([x0, x1])
    return [Segment(x0, x1) for x0, x1 in segments]
