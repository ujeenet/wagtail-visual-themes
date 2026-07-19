"""Pure-function tests for color helpers — no DB required."""

import pytest

from wagtail_themes.color_utils import (
    best_contrast,
    contrast_ratio,
    derive_shades,
    is_gradient,
    parse_rgb_triplet,
    relative_luminance,
    wcag_grade,
)


def test_parse_rgb_triplet_hex_3() -> None:
    assert parse_rgb_triplet("#fff") == (255, 255, 255)


def test_parse_rgb_triplet_hex_6() -> None:
    assert parse_rgb_triplet("#0f172a") == (15, 23, 42)


def test_parse_rgb_triplet_rgb_function() -> None:
    assert parse_rgb_triplet("rgb(34, 51, 68)") == (34, 51, 68)


def test_parse_rgb_triplet_rgba_function() -> None:
    assert parse_rgb_triplet("rgba(10, 20, 30, 0.5)") == (10, 20, 30)


def test_parse_rgb_triplet_returns_none_for_gradient() -> None:
    assert parse_rgb_triplet("linear-gradient(90deg, red, blue)") is None


def test_is_gradient_true() -> None:
    assert is_gradient("linear-gradient(red, blue)") is True
    assert is_gradient("radial-gradient(red, blue)") is True


def test_is_gradient_false() -> None:
    assert is_gradient("#ff0000") is False
    assert is_gradient("rgb(255, 0, 0)") is False


def test_best_contrast_white_for_dark_color() -> None:
    assert best_contrast("#000000") == "#ffffff"
    assert best_contrast("#0f172a") == "#ffffff"


def test_best_contrast_black_for_light_color() -> None:
    assert best_contrast("#ffffff") == "#000000"
    assert best_contrast("#fef3c7") == "#000000"


def test_relative_luminance_extremes() -> None:
    assert relative_luminance((0, 0, 0)) == 0.0
    assert relative_luminance((255, 255, 255)) == 1.0


# --- Named colors (issue #6) ---------------------------------------------


def test_parse_rgb_triplet_named_color() -> None:
    assert parse_rgb_triplet("white") == (255, 255, 255)
    assert parse_rgb_triplet("black") == (0, 0, 0)
    assert parse_rgb_triplet("red") == (255, 0, 0)
    assert parse_rgb_triplet("rebeccapurple") == (102, 51, 153)


def test_parse_rgb_triplet_named_color_case_insensitive() -> None:
    assert parse_rgb_triplet("White") == (255, 255, 255)
    assert parse_rgb_triplet("  REBECCAPURPLE ") == (102, 51, 153)


def test_parse_rgb_triplet_named_grey_spelling() -> None:
    assert parse_rgb_triplet("gray") == parse_rgb_triplet("grey")


def test_named_color_gets_shades_and_rgb() -> None:
    """Regression for #6: named colors must derive a full shade scale."""
    shades = derive_shades("rebeccapurple")
    assert len(shades) == 11


# --- hsl() / hsla() (issue #6) -------------------------------------------


def test_parse_rgb_triplet_hsl_comma_syntax() -> None:
    # hsl(0, 100%, 50%) is pure red.
    assert parse_rgb_triplet("hsl(0, 100%, 50%)") == (255, 0, 0)


def test_parse_rgb_triplet_hsl_space_syntax() -> None:
    assert parse_rgb_triplet("hsl(120 100% 50%)") == (0, 255, 0)


def test_parse_rgb_triplet_hsl_with_deg_and_alpha() -> None:
    assert parse_rgb_triplet("hsla(240deg, 100%, 50%, 0.5)") == (0, 0, 255)


def test_hsl_gets_shades() -> None:
    assert len(derive_shades("hsl(217 91% 60%)")) == 11


def test_parse_rgb_triplet_still_none_for_unknown() -> None:
    assert parse_rgb_triplet("not-a-color") is None
    assert parse_rgb_triplet("bananas") is None
    # oklch() is not supported yet — must degrade to None, never crash.
    assert parse_rgb_triplet("oklch(0.7 0.15 250)") is None


# --- Contrast ratio + WCAG grading (issue #5) ----------------------------


def test_contrast_ratio_black_on_white_is_max() -> None:
    assert round(contrast_ratio("#000000", "#ffffff"), 1) == 21.0


def test_contrast_ratio_is_symmetric() -> None:
    assert contrast_ratio("#000", "#fff") == contrast_ratio("#fff", "#000")


def test_contrast_ratio_identical_colors_is_one() -> None:
    assert contrast_ratio("#3b82f6", "#3b82f6") == pytest.approx(1.0)


def test_contrast_ratio_none_when_unparseable() -> None:
    assert contrast_ratio("linear-gradient(red, blue)", "#fff") is None
    assert contrast_ratio("#fff", "oklch(0.7 0.15 250)") is None


def test_contrast_ratio_accepts_named_colors() -> None:
    assert round(contrast_ratio("black", "white"), 1) == 21.0


@pytest.mark.parametrize(
    ("ratio", "large", "expected"),
    [
        (21.0, False, "AAA"),
        (7.0, False, "AAA"),
        (6.9, False, "AA"),
        (4.5, False, "AA"),
        (4.49, False, "Fail"),
        (3.0, True, "AA"),
        (4.5, True, "AAA"),
        (2.9, True, "Fail"),
        (None, False, "n/a"),
    ],
)
def test_wcag_grade(ratio, large, expected) -> None:
    assert wcag_grade(ratio, large_text=large) == expected
