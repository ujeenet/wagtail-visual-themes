"""Tests for theme resolution logic (page tree, site, default)."""

import pytest
from wagtail.models import Page

from tests.app.models import ThemedTestPage
from wagtail_themes.models import Theme
from wagtail_themes.resolver import resolve_theme_for_page


@pytest.mark.django_db
def test_resolver_returns_pages_own_theme() -> None:
    theme = Theme.objects.create(name="Local", slug="local")
    root = Page.objects.get(depth=1)
    page = root.add_child(
        instance=ThemedTestPage(title="Page", slug="page", theme=theme)
    )
    assert resolve_theme_for_page(page) == theme


@pytest.mark.django_db
def test_resolver_walks_to_ancestor() -> None:
    theme = Theme.objects.create(name="Inherited", slug="inherited")
    root = Page.objects.get(depth=1)
    parent = root.add_child(
        instance=ThemedTestPage(title="Parent", slug="parent", theme=theme)
    )
    child = parent.add_child(
        instance=ThemedTestPage(title="Child", slug="child")
    )
    assert resolve_theme_for_page(child) == theme


@pytest.mark.django_db
def test_resolver_falls_back_to_default_theme() -> None:
    default = Theme.objects.create(name="Fallback", slug="fallback", is_default=True)
    root = Page.objects.get(depth=1)
    page = root.add_child(
        instance=ThemedTestPage(title="Page", slug="page")
    )
    assert resolve_theme_for_page(page) == default


@pytest.mark.django_db
def test_resolver_returns_none_when_nothing_set() -> None:
    root = Page.objects.get(depth=1)
    page = root.add_child(
        instance=ThemedTestPage(title="Page", slug="page")
    )
    assert resolve_theme_for_page(page) is None
