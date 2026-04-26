"""Tests for HSL-based 50→950 shade derivation."""

from wagtail_themes.color_utils import (
    derive_shades,
    hsl_to_rgb,
    rgb_to_hsl,
)


def test_rgb_to_hsl_white():
    h, s, light = rgb_to_hsl(255, 255, 255)
    assert s == 0.0
    assert light == 1.0


def test_rgb_to_hsl_black():
    h, s, light = rgb_to_hsl(0, 0, 0)
    assert s == 0.0
    assert light == 0.0


def test_rgb_to_hsl_pure_red():
    h, s, light = rgb_to_hsl(255, 0, 0)
    assert h == 0.0
    assert round(s, 3) == 1.0
    assert round(light, 3) == 0.5


def test_rgb_hsl_roundtrip():
    """For a few real-world colors, RGB → HSL → RGB should be near-identity."""
    for original in [(59, 130, 246), (220, 38, 38), (245, 158, 11)]:
        h, s, light = rgb_to_hsl(*original)
        roundtripped = hsl_to_rgb(h, s, light)
        for o, r in zip(original, roundtripped, strict=True):
            assert abs(o - r) <= 1, f"{original} → {roundtripped}"


def test_derive_shades_returns_full_scale_for_solid():
    shades = derive_shades("#3b82f6")
    expected_keys = {"50", "100", "200", "300", "400", "500",
                     "600", "700", "800", "900", "950"}
    assert set(shades.keys()) == expected_keys


def test_derive_shades_pins_500_to_source():
    shades = derive_shades("#3b82f6")
    assert shades["500"].lower() == "#3b82f6"


def test_derive_shades_lighter_to_darker_by_luminance():
    """Lower keys should be lighter, higher keys should be darker."""
    from wagtail_themes.color_utils import parse_rgb_triplet, relative_luminance

    shades = derive_shades("#3b82f6")
    luminances = [
        relative_luminance(parse_rgb_triplet(shades[k]))
        for k in ["50", "100", "200", "300", "400", "500",
                  "600", "700", "800", "900", "950"]
    ]
    for a, b in zip(luminances, luminances[1:], strict=False):
        assert a > b, f"luminance not strictly decreasing: {luminances}"


def test_derive_shades_returns_empty_for_gradient():
    assert derive_shades("linear-gradient(red, blue)") == {}


def test_derive_shades_returns_empty_for_invalid():
    assert derive_shades("") == {}
    assert derive_shades("not-a-color") == {}
