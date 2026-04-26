"""Helpers for parsing colors and computing CSS-variable-friendly forms."""

from __future__ import annotations

import re

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB_RE = re.compile(
    r"^rgba?\(\s*(\d+)\s*,?\s*(\d+)\s*,?\s*(\d+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$"
)


def parse_rgb_triplet(value: str) -> tuple[int, int, int] | None:
    """Parse a hex or rgb() string into an (r, g, b) triplet.

    Returns None for gradients or values we can't parse — those will fall back
    to direct CSS output rather than RGB-triplet variables.
    """
    if not value:
        return None
    value = value.strip()

    hex_match = _HEX_RE.match(value)
    if hex_match:
        digits = hex_match.group(1)
        if len(digits) == 3:
            r, g, b = (int(c * 2, 16) for c in digits)
        elif len(digits) == 8:
            r = int(digits[0:2], 16)
            g = int(digits[2:4], 16)
            b = int(digits[4:6], 16)
        else:
            r = int(digits[0:2], 16)
            g = int(digits[2:4], 16)
            b = int(digits[4:6], 16)
        return r, g, b

    rgb_match = _RGB_RE.match(value)
    if rgb_match:
        return (
            int(rgb_match.group(1)),
            int(rgb_match.group(2)),
            int(rgb_match.group(3)),
        )

    return None


def is_gradient(value: str) -> bool:
    if not value:
        return False
    return "gradient(" in value.lower()


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance for an sRGB triplet (0-255)."""

    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def best_contrast(value: str) -> str:
    """Pick #ffffff or #000000 against a solid color, defaulting to #ffffff."""
    rgb = parse_rgb_triplet(value)
    if rgb is None:
        return "#ffffff"
    return "#000000" if relative_luminance(rgb) > 0.5 else "#ffffff"
