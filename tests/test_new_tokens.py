"""Tests for newly-emitted token scales (spacing, font-size, leading,
tracking, border widths, z-index, transitions, state overlays)."""

import pytest

from wagtail_themes.models import BrandColor, Theme


@pytest.fixture
def theme(db) -> Theme:
    t = Theme.objects.create(name="T", slug="t")
    BrandColor.objects.create(theme=t, name="Primary", color_value="#3b82f6")
    return t


@pytest.mark.django_db
def test_spacing_scale_emitted(theme: Theme):
    css = theme.emit_css()
    assert "--space-0: 0;" in css
    assert "--space-px: 1px;" in css
    assert "--space-4: 1rem;" in css
    assert "--space-12: 3rem;" in css
    assert "--space-24: 6rem;" in css


@pytest.mark.django_db
def test_font_size_modular_scale(theme: Theme):
    css = theme.emit_css()
    assert "--font-size-xs: 0.75rem;" in css
    assert "--font-size-sm: 0.875rem;" in css
    assert "--font-size-base: " in css  # in px from font_scale
    assert "--font-size-lg: 1.125rem;" in css
    assert "--font-size-xl: 1.25rem;" in css
    assert "--font-size-2xl: 1.5rem;" in css
    assert "--font-size-3xl: 1.875rem;" in css
    assert "--font-size-4xl: 2.25rem;" in css


@pytest.mark.django_db
def test_leading_and_tracking_emitted(theme: Theme):
    css = theme.emit_css()
    assert "--leading-tight: 1.25;" in css
    assert "--leading-normal: 1.5;" in css
    assert "--leading-relaxed: 1.75;" in css
    assert "--tracking-tight: -0.025em;" in css
    assert "--tracking-normal: 0em;" in css
    assert "--tracking-wide: 0.05em;" in css


@pytest.mark.django_db
def test_border_widths(theme: Theme):
    css = theme.emit_css()
    assert "--border-1: 1px;" in css
    assert "--border-2: 2px;" in css
    assert "--border-4: 4px;" in css
    assert "--border-8: 8px;" in css


@pytest.mark.django_db
def test_z_index_scale(theme: Theme):
    css = theme.emit_css()
    for name, value in (
        ("base", 0),
        ("dropdown", 10),
        ("sticky", 20),
        ("fixed", 30),
        ("overlay", 40),
        ("modal", 50),
        ("popover", 60),
        ("tooltip", 70),
        ("toast", 80),
    ):
        assert f"--z-{name}: {value};" in css


@pytest.mark.django_db
def test_transitions(theme: Theme):
    css = theme.emit_css()
    assert "--duration-fast: 150ms;" in css
    assert "--duration-normal: 200ms;" in css
    assert "--duration-slow: 300ms;" in css
    assert "--ease-out: cubic-bezier(0, 0, 0.2, 1);" in css
    assert "--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);" in css


@pytest.mark.django_db
def test_state_overlays(theme: Theme):
    css = theme.emit_css()
    assert "--state-hover-overlay: 0.08;" in css
    assert "--state-active-overlay: 0.16;" in css
    assert "--state-disabled-opacity: 0.5;" in css


@pytest.mark.django_db
def test_brand_color_emits_full_shade_scale(theme: Theme):
    css = theme.emit_css()
    # Base + every shade for the Primary brand color
    for shade in ("50", "100", "200", "300", "400", "500",
                  "600", "700", "800", "900", "950"):
        assert f"--color-primary-{shade}:" in css, f"missing shade {shade}"


@pytest.mark.django_db
def test_brand_color_shade_emits_rgb_companion(theme: Theme):
    """Each shade should also have a -rgb companion so Tailwind opacity
    utilities (e.g. `bg-primary-100/50`) work."""
    css = theme.emit_css()
    for shade in ("50", "500", "900"):
        assert f"--color-primary-{shade}-rgb:" in css


@pytest.mark.django_db
def test_gradient_brand_color_skips_shade_scale():
    t = Theme.objects.create(name="G", slug="g")
    BrandColor.objects.create(
        theme=t, name="Hero",
        color_value="linear-gradient(90deg, red, blue)",
    )
    css = t.emit_css()
    # The base variable still emits …
    assert "--color-hero: linear-gradient(90deg, red, blue);" in css
    # … but no derived shade scale.
    assert "--color-hero-50:" not in css
    assert "--color-hero-500:" not in css


def test_unsaved_theme_emits_all_new_token_groups():
    """Regression: the new emitter additions must also tolerate unsaved
    Theme instances (used by the snippet preview)."""
    css = Theme(name="X", slug="x").emit_css()
    assert "--space-4:" in css
    assert "--leading-tight:" in css
    assert "--z-modal:" in css
    assert "--duration-normal:" in css
    assert "--state-hover-overlay:" in css
    # Brand-color shades aren't emitted when no brand colors exist
    assert "--color-primary-100:" not in css
