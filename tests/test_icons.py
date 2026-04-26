"""Tests for the custom palette icon registration."""

from django.template.loader import get_template
from wagtail import hooks


def test_palette_svg_template_is_findable():
    """Wagtail's render_icon resolves icons via Django's template loader, so
    the SVG must be discoverable at the registered path."""
    tpl = get_template("wagtailadmin/icons/wagtail-themes-palette.svg")
    rendered = tpl.render({})
    assert 'id="icon-wagtail-themes-palette"' in rendered
    assert "<svg" in rendered
    assert 'viewBox="0 0 16 16"' in rendered


def test_register_icons_hook_includes_palette():
    """The register_icons hook must add the package's SVG to Wagtail's
    icon list — that's how custom icon names become resolvable."""
    fns = hooks.get_hooks("register_icons")
    assert fns, "no register_icons hooks registered"

    aggregated: list[str] = []
    for fn in fns:
        aggregated = fn(aggregated)

    assert "wagtailadmin/icons/wagtail-themes-palette.svg" in aggregated


def test_theme_viewset_uses_palette_icon():
    from wagtail_themes.viewsets import (
        PALETTE_ICON,
        ThemeViewSet,
        WagtailThemesViewSetGroup,
    )

    assert PALETTE_ICON == "wagtail-themes-palette"
    assert ThemeViewSet.icon == PALETTE_ICON
    assert WagtailThemesViewSetGroup.menu_icon == PALETTE_ICON


def test_icon_renders_through_wagtail_template_tag():
    """Wagtail's `{% icon %}` tag emits a `<use href="#icon-…">` reference;
    the actual <symbol> definitions are injected as a sprite by the admin
    template. We assert the reference is wired up correctly."""
    from django.template import Context, Template

    tpl = Template(
        "{% load wagtailadmin_tags %}{% icon name='wagtail-themes-palette' %}"
    )
    rendered = tpl.render(Context({}))
    assert 'href="#icon-wagtail-themes-palette"' in rendered
    assert "icon-wagtail-themes-palette" in rendered


def test_palette_appears_in_admin_icon_sprite():
    """Belt-and-braces: our SVG is bundled into Wagtail's admin sprite,
    so the `<use href="#icon-wagtail-themes-palette">` reference resolves."""
    from wagtail.admin.icons import get_icons

    sprite = get_icons()
    assert 'id="icon-wagtail-themes-palette"' in sprite
