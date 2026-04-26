"""Pure-function tests for color helpers — no DB required."""

from wagtail_themes.color_utils import (
    best_contrast,
    is_gradient,
    parse_rgb_triplet,
    relative_luminance,
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
