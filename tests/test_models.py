"""Tests for Theme + BrandColor models and CSS emission."""

import pytest
from django.template.loader import render_to_string

from wagtail_themes.models import BrandColor, Theme


@pytest.fixture
def theme(db) -> Theme:
    return Theme.objects.create(name="Default", slug="default")


def test_contrast_report_grades_default_pairs() -> None:
    """contrast_report works on an unsaved Theme (no DB) and grades each pair."""
    t = Theme(name="X", slug="x")  # model field defaults
    report = t.contrast_report(dark=False)

    assert [r["label"] for r in report] == [
        "Text primary on background",
        "Text primary on surface",
        "Text secondary on background",
        "Text secondary on surface",
        "Text muted on background",
        "Link on background",
    ]
    by_label = {r["label"]: r for r in report}
    # Default primary text (#0f172a) on white is very high contrast.
    assert by_label["Text primary on background"]["grade"] == "AAA"
    assert by_label["Text primary on background"]["passes"] is True
    # Default muted text (#94a3b8) on white fails AA — the whole point of the badge.
    assert by_label["Text muted on background"]["grade"] == "Fail"
    assert by_label["Text muted on background"]["passes"] is False


def test_contrast_report_dark_mode_uses_dark_values() -> None:
    t = Theme(name="X", slug="x")
    dark = t.contrast_report(dark=True)
    by_label = {r["label"]: r for r in dark}
    # Dark primary text on dark bg should still pass.
    assert by_label["Text primary on background"]["passes"] is True


def test_preview_brand_colors_empty_for_unsaved() -> None:
    # Reading the reverse relation on an unsaved theme would raise; guard it.
    assert Theme(name="X", slug="x").preview_brand_colors() == []


def test_preview_context_does_not_crash_for_unsaved() -> None:
    ctx = Theme(name="X", slug="x").get_preview_context(None, "light")
    assert ctx["brand_colors"] == []
    assert "contrast_report" in ctx


def test_preview_template_renders_for_unsaved_theme() -> None:
    """Regression: the preview must not 500 for a new/unsaved theme (#borders-shadows)."""
    theme = Theme(name="New", slug="new")
    ctx = theme.get_preview_context(None, "light")
    html = render_to_string("wagtail_themes/preview/theme_preview.html", ctx)
    # The whole preview renders (borders/shadows sections present), no brand section.
    assert "Border radii" in html
    assert "Shadows" in html
    assert "Brand colors" not in html


@pytest.mark.django_db
def test_preview_brand_colors_lists_active_with_shades() -> None:
    theme = Theme.objects.create(name="T", slug="t")
    BrandColor.objects.create(theme=theme, name="Primary", color_value="#3b82f6")
    BrandColor.objects.create(
        theme=theme, name="Warm", color_value="linear-gradient(90deg, red, blue)"
    )
    BrandColor.objects.create(
        theme=theme, name="Old", color_value="#111111", is_active=False
    )

    colors = {c["name"]: c for c in theme.preview_brand_colors()}
    assert set(colors) == {"Primary", "Warm"}  # inactive excluded
    assert len(colors["Primary"]["shades"]) == 11  # solid → full ramp
    assert colors["Warm"]["shades"] == []  # gradient → no shades
    assert colors["Warm"]["is_gradient"] is True


@pytest.mark.django_db
def test_preview_brand_colors_dark_mode_uses_dark_value() -> None:
    theme = Theme.objects.create(name="T", slug="t")
    BrandColor.objects.create(
        theme=theme, name="Primary", color_value="#3b82f6", color_value_dark="#1e3a8a"
    )
    light = theme.preview_brand_colors(dark=False)[0]
    dark = theme.preview_brand_colors(dark=True)[0]
    assert light["value"] == "#3b82f6"
    assert dark["value"] == "#1e3a8a"


@pytest.mark.django_db
def test_preview_template_renders_brand_shades_for_saved_theme() -> None:
    theme = Theme.objects.create(name="T", slug="t")
    BrandColor.objects.create(theme=theme, name="Primary", color_value="rebeccapurple")
    ctx = theme.get_preview_context(None, "light")
    html = render_to_string("wagtail_themes/preview/theme_preview.html", ctx)
    assert "Brand colors" in html
    assert "--color-primary" in html


def test_contrast_report_handles_gradient_link() -> None:
    t = Theme(name="X", slug="x", link_color="linear-gradient(90deg, red, blue)")
    by_label = {r["label"]: r for r in t.contrast_report()}
    link = by_label["Link on background"]
    assert link["ratio"] is None
    assert link["grade"] == "n/a"
    assert link["passes"] is False


@pytest.mark.django_db
def test_theme_str() -> None:
    t = Theme.objects.create(name="Marketing", slug="marketing")
    assert str(t) == "Marketing"


@pytest.mark.django_db
def test_theme_is_default_enforces_singleton() -> None:
    t1 = Theme.objects.create(name="A", slug="a", is_default=True)
    t2 = Theme.objects.create(name="B", slug="b", is_default=True)
    t1.refresh_from_db()
    assert t1.is_default is False
    assert t2.is_default is True


@pytest.mark.django_db
def test_theme_get_default_returns_default() -> None:
    Theme.objects.create(name="A", slug="a")
    default = Theme.objects.create(name="B", slug="b", is_default=True)
    assert Theme.get_default() == default


@pytest.mark.django_db
def test_brand_color_slug_and_var_name(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme, name="Primary Brand", color_value="#3b82f6"
    )
    assert color.slug == "primary-brand"
    assert color.css_var_name == "--color-primary-brand"


@pytest.mark.django_db
def test_brand_color_contrast_picks_white_for_dark(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme, name="Primary", color_value="#0f172a"
    )
    assert color.contrast_color == "#ffffff"


@pytest.mark.django_db
def test_brand_color_contrast_picks_black_for_light(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme, name="Primary", color_value="#fef3c7"
    )
    assert color.contrast_color == "#000000"


@pytest.mark.django_db
def test_brand_color_dark_value_falls_back_to_light(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme, name="Primary", color_value="#3b82f6"
    )
    assert color.effective_dark_value == "#3b82f6"


@pytest.mark.django_db
def test_brand_color_dark_value_uses_override(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme,
        name="Primary",
        color_value="#3b82f6",
        color_value_dark="#1e3a8a",
    )
    assert color.effective_dark_value == "#1e3a8a"


@pytest.mark.django_db
def test_brand_color_rgb_triplet_for_solid(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme, name="Primary", color_value="#3b82f6"
    )
    assert color.rgb_triplet == "59 130 246"


@pytest.mark.django_db
def test_brand_color_rgb_triplet_none_for_gradient(theme: Theme) -> None:
    color = BrandColor.objects.create(
        theme=theme,
        name="Hero",
        color_value="linear-gradient(90deg, #f00, #00f)",
    )
    assert color.rgb_triplet is None


@pytest.mark.django_db
def test_emit_css_contains_root_dark_and_system_blocks(theme: Theme) -> None:
    BrandColor.objects.create(theme=theme, name="Primary", color_value="#3b82f6")
    css = theme.emit_css()
    assert ":root {" in css
    assert '[data-theme="dark"] {' in css
    assert '@media (prefers-color-scheme: dark)' in css
    assert '[data-theme="system"]' in css


@pytest.mark.django_db
def test_emit_css_emits_brand_color_rgb_companion(theme: Theme) -> None:
    BrandColor.objects.create(theme=theme, name="Primary", color_value="#3b82f6")
    css = theme.emit_css()
    assert "--color-primary: #3b82f6" in css
    assert "--color-primary-rgb: 59 130 246" in css
    assert "--color-primary-contrast:" in css


@pytest.mark.django_db
def test_emit_css_skips_inactive_brand_colors(theme: Theme) -> None:
    BrandColor.objects.create(theme=theme, name="Primary", color_value="#3b82f6")
    BrandColor.objects.create(
        theme=theme, name="Retired", color_value="#000000", is_active=False
    )
    css = theme.emit_css()
    assert "--color-primary:" in css
    assert "--color-retired" not in css


@pytest.mark.django_db
def test_emit_css_includes_radii_and_shadows(theme: Theme) -> None:
    css = theme.emit_css()
    assert "--radius-sm:" in css
    assert "--radius-md:" in css
    assert "--radius-full:" in css
    assert "--shadow-sm:" in css
    assert "--shadow-lg:" in css


@pytest.mark.django_db
def test_emit_css_typography(theme: Theme) -> None:
    css = theme.emit_css()
    assert "--font-heading:" in css
    assert "--font-body:" in css
    assert "--font-size-base:" in css


def test_emit_css_works_for_unsaved_theme_preview() -> None:
    """Wagtail's snippet preview renders an unsaved instance built from form
    data. Reverse relations (brand_colors) raise without a pk, so emit_css
    must skip them rather than crash.
    """
    theme = Theme(name="Draft", slug="draft")  # not saved → pk is None
    css = theme.emit_css()
    assert ":root {" in css
    assert "--color-bg:" in css
    assert "--radius-md:" in css
