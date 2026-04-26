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


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert sRGB (0-255) → HSL with H in [0,360), S/L in [0,1]."""
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    cmax = max(rn, gn, bn)
    cmin = min(rn, gn, bn)
    delta = cmax - cmin
    light = (cmax + cmin) / 2.0
    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        s = delta / (1 - abs(2 * light - 1)) if light else 0.0
        if cmax == rn:
            h = ((gn - bn) / delta) % 6
        elif cmax == gn:
            h = ((bn - rn) / delta) + 2
        else:
            h = ((rn - gn) / delta) + 4
        h *= 60.0
    return h, s, light


def hsl_to_rgb(h: float, s: float, light: float) -> tuple[int, int, int]:
    """Convert HSL → sRGB triplet (0-255)."""
    c = (1 - abs(2 * light - 1)) * s
    h_prime = (h % 360) / 60.0
    x = c * (1 - abs(h_prime % 2 - 1))
    if 0 <= h_prime < 1:
        r1, g1, b1 = c, x, 0.0
    elif 1 <= h_prime < 2:
        r1, g1, b1 = x, c, 0.0
    elif 2 <= h_prime < 3:
        r1, g1, b1 = 0.0, c, x
    elif 3 <= h_prime < 4:
        r1, g1, b1 = 0.0, x, c
    elif 4 <= h_prime < 5:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x
    m = light - c / 2
    return (
        max(0, min(255, round((r1 + m) * 255))),
        max(0, min(255, round((g1 + m) * 255))),
        max(0, min(255, round((b1 + m) * 255))),
    )


# Tailwind-style 50→950 lightness targets. The base color is pinned to 500;
# lighter shades trend toward white, darker toward near-black, all sharing
# the source hue and (mostly) the source saturation.
SHADE_LIGHTNESS = {
    "50": 0.97,
    "100": 0.93,
    "200": 0.86,
    "300": 0.74,
    "400": 0.62,
    "500": None,  # pinned to source
    "600": 0.42,
    "700": 0.32,
    "800": 0.24,
    "900": 0.16,
    "950": 0.10,
}


def derive_shades(value: str) -> dict[str, str]:
    """Return Tailwind-style 50→950 hex shades for a solid color.

    Falls back to an empty dict for gradients or non-hex inputs.
    """
    rgb = parse_rgb_triplet(value)
    if rgb is None:
        return {}
    h, s, light_source = rgb_to_hsl(*rgb)

    out: dict[str, str] = {}
    for key, target_l in SHADE_LIGHTNESS.items():
        if target_l is None:
            shade_rgb = rgb
        else:
            # Soften saturation at the extremes so 50/100 don't look neon-tinted
            # and 900/950 don't look unnaturally chromatic.
            if target_l > 0.85:
                sat = s * 0.5
            elif target_l < 0.25:
                sat = s * 0.7
            else:
                sat = s
            shade_rgb = hsl_to_rgb(h, sat, target_l)
        out[key] = "#{:02x}{:02x}{:02x}".format(*shade_rgb)
    return out
