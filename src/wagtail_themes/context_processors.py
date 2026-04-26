"""Context processor that exposes the active theme to all templates."""

from __future__ import annotations

from typing import Any

from .resolver import resolve_theme_for_request


def active_theme(request: Any) -> dict[str, Any]:
    """Add `active_theme` to the template context.

    Add `wagtail_themes.context_processors.active_theme` to your
    TEMPLATES[OPTIONS][context_processors] to use it.
    """
    theme = resolve_theme_for_request(request)
    return {"active_theme": theme}
