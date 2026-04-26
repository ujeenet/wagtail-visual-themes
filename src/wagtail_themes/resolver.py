"""Resolve the active Theme for a request, page, or site."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.apps import apps

if TYPE_CHECKING:
    from wagtail.models import Page, Site

    from .models import Theme


def _get_theme_model() -> type[Theme]:
    return apps.get_model("wagtail_themes", "Theme")


def resolve_theme_for_page(page: Page) -> Theme | None:
    """Walk up the tree, return the first ancestor's theme that's set.

    Falls back to the Site setting (if installed), then to the default Theme.
    """
    current: Page | None = page
    while current is not None:
        theme = getattr(current, "theme", None)
        if theme is not None:
            return theme
        current = current.get_parent() if current.depth and current.depth > 1 else None

    site = getattr(page, "_site_cached", None) or _site_for_page(page)
    if site is not None:
        site_theme = resolve_theme_for_site(site)
        if site_theme is not None:
            return site_theme

    return _get_theme_model().get_default()


def _site_for_page(page: Page) -> Site | None:
    try:
        return page.get_site()
    except Exception:  # noqa: BLE001
        return None


def resolve_theme_for_site(site: Site) -> Theme | None:
    """Resolve via ThemeSiteSetting if `wagtail.contrib.settings` is installed."""
    try:
        from .settings import ThemeSiteSetting
    except Exception:  # noqa: BLE001
        return None

    try:
        setting = ThemeSiteSetting.for_site(site)
    except Exception:  # noqa: BLE001
        return None

    return getattr(setting, "theme", None)


def resolve_theme_for_request(request: Any) -> Theme | None:
    """Best-effort theme resolver based on the current request.

    Looks for `request.active_theme` (if some upstream code already set it),
    then the matching Wagtail Site, then the default Theme.
    """
    pre = getattr(request, "active_theme", None)
    if pre is not None:
        return pre

    try:
        from wagtail.models import Site

        site = Site.find_for_request(request)
    except Exception:  # noqa: BLE001
        site = None

    if site is not None:
        site_theme = resolve_theme_for_site(site)
        if site_theme is not None:
            return site_theme

    return _get_theme_model().get_default()
