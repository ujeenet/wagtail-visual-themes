"""Template tags for injecting themes into templates."""

from __future__ import annotations

from typing import Any

from django import template
from django.utils.safestring import mark_safe

from ..resolver import resolve_theme_for_request

register = template.Library()


def _resolve_theme(context: dict[str, Any]):
    theme = context.get("active_theme")
    if theme is not None:
        return theme

    page = context.get("page")
    if page is not None and hasattr(page, "get_active_theme"):
        try:
            theme = page.get_active_theme()
        except Exception:  # noqa: BLE001
            theme = None
        if theme is not None:
            return theme

    request = context.get("request")
    if request is not None:
        return resolve_theme_for_request(request)

    return None


def _fallback_theme():
    """An in-memory Theme using the model's baked-in field defaults.

    Returned when no Theme is configured (no `is_default=True` row, no Site
    setting, no page-level FK). Lets `{% theme_css %}` always emit a usable
    set of variables so consumer CSS never breaks on a fresh install.
    """
    from ..models import Theme

    return Theme(name="Default", slug="default")


@register.simple_tag(takes_context=True)
def theme_css(
    context,
    theme=None,
    include_style_tag=True,
    include_fonts=True,
    fallback=True,
):
    """Render the active theme's CSS variables as a `<style>` block.

    Usage:
        {% load wagtail_themes %}
        <head>
            {% theme_css %}
        </head>

    Pass `theme=...` to override resolution. Pass `include_style_tag=False`
    to get just the CSS body (useful inside a custom <style> tag). Pass
    `fallback=False` to emit nothing when no Theme is configured (default
    behaviour is to emit an in-memory Theme's defaults so styles never
    silently break).
    """
    if theme is None:
        theme = _resolve_theme(context)
    if theme is None:
        if not fallback:
            return ""
        theme = _fallback_theme()

    css_body = theme.emit_css()
    parts: list[str] = []
    if include_fonts and theme.custom_fonts_css_url:
        parts.append(
            f'<link rel="stylesheet" href="{theme.custom_fonts_css_url}">'
        )
    if include_style_tag:
        parts.append(f"<style>{css_body}</style>")
    else:
        parts.append(css_body)
    return mark_safe("\n".join(parts))


@register.simple_tag(takes_context=True)
def theme_html_attrs(context, theme=None, fallback=True):
    """Render the `data-theme="…"` attribute (and class) for `<html>`.

    Usage:
        <html {% theme_html_attrs %}>

    Falls back to the in-memory default Theme so `data-theme="system"` is
    always set — without it, the `[data-theme="dark"]` selectors emitted by
    `{% theme_css %}` never apply and the switcher cannot toggle modes.
    Pass `fallback=False` to opt out.
    """
    if theme is None:
        theme = _resolve_theme(context)
    if theme is None:
        if not fallback:
            return ""
        theme = _fallback_theme()
    parts = [
        f'data-theme="{theme.default_mode}"',
        f'data-theme-name="{theme.slug}"',
        f'class="theme-{theme.slug}"',
    ]
    return mark_safe(" ".join(parts))


@register.inclusion_tag("wagtail_themes/no_flash.html", takes_context=True)
def theme_no_flash(context):
    """Inline JS that applies the saved theme mode before paint (no FOUC)."""
    return {}


@register.inclusion_tag("wagtail_themes/switcher.html", takes_context=True)
def theme_switcher(context):
    """A minimal theme-mode toggle (light / dark / system)."""
    theme = _resolve_theme(context)
    return {"theme": theme}
