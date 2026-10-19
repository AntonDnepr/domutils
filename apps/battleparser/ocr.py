"""Text recognition of single table cells with Tesseract (classic local OCR)."""

import cv2
import numpy as np
import pytesseract

# Row height (px) that Tesseract reads best for this font; crops are scaled to it.
TARGET_ROW_HEIGHT = 56
TEXT_CONFIG = "--psm 7"


def _prepare(binary: np.ndarray, row_height: int) -> np.ndarray:
    """Black text on white, scaled to the target height and padded."""
    image = np.where(binary, 0, 255).astype(np.uint8)
    scale = TARGET_ROW_HEIGHT / max(1, row_height)
    if abs(scale - 1) > 0.1:
        image = cv2.resize(
            image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
        image = np.where(image > 127, 255, 0).astype(np.uint8)
    pad = TARGET_ROW_HEIGHT // 2
    return cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)


def read_text(binary: np.ndarray, row_height: int) -> str:
    text = pytesseract.image_to_string(_prepare(binary, row_height), config=TEXT_CONFIG)
    return " ".join(text.split())
