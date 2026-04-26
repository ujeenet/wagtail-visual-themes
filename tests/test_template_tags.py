"""Tests for `{% theme_css %}` and `{% theme_html_attrs %}` template tags."""

import pytest
from django.template import Context, Template

from wagtail_themes.models import BrandColor, Theme


@pytest.fixture
def theme(db) -> Theme:
    t = Theme.objects.create(name="Default", slug="default")
    BrandColor.objects.create(theme=t, name="Primary", color_value="#3b82f6")
    return t


@pytest.mark.django_db
def test_theme_css_renders_style_block(theme: Theme) -> None:
    template = Template("{% load wagtail_themes %}{% theme_css %}")
    rendered = template.render(Context({"active_theme": theme}))
    assert "<style>" in rendered
    assert "--color-primary: #3b82f6" in rendered
    assert "</style>" in rendered


@pytest.mark.django_db
def test_theme_css_can_skip_style_tag(theme: Theme) -> None:
    template = Template(
        "{% load wagtail_themes %}{% theme_css include_style_tag=False %}"
    )
    rendered = template.render(Context({"active_theme": theme}))
    assert "<style>" not in rendered
    assert "--color-primary" in rendered


@pytest.mark.django_db
def test_theme_css_includes_custom_fonts_link(theme: Theme) -> None:
    theme.custom_fonts_css_url = "https://fonts.example.com/css?family=Inter"
    theme.save()
    template = Template("{% load wagtail_themes %}{% theme_css %}")
    rendered = template.render(Context({"active_theme": theme}))
    assert 'href="https://fonts.example.com/css?family=Inter"' in rendered


@pytest.mark.django_db
def test_theme_html_attrs(theme: Theme) -> None:
    template = Template("{% load wagtail_themes %}{% theme_html_attrs %}")
    rendered = template.render(Context({"active_theme": theme}))
    assert 'data-theme="system"' in rendered
    assert 'data-theme-name="default"' in rendered
    assert 'class="theme-default"' in rendered


def test_theme_css_emits_fallback_when_no_theme_configured() -> None:
    """Without a Theme in the database, `{% theme_css %}` defaults to an
    in-memory Theme so consumer CSS variables stay defined. Reason: a fresh
    install would otherwise render unstyled until the user creates the first
    Theme, which is a poor first-run experience."""
    template = Template("{% load wagtail_themes %}{% theme_css %}")
    rendered = template.render(Context({}))
    assert "<style>" in rendered
    # Surface defaults from the Theme model field defaults
    assert "--color-bg: #ffffff" in rendered
    assert "--color-text-primary: #0f172a" in rendered
    assert '[data-theme="dark"] {' in rendered
    assert "--radius-md:" in rendered
    assert "--shadow-md:" in rendered


def test_theme_css_can_opt_out_of_fallback() -> None:
    template = Template(
        "{% load wagtail_themes %}{% theme_css fallback=False %}"
    )
    rendered = template.render(Context({}))
    assert rendered.strip() == ""


def test_theme_html_attrs_emits_fallback_when_no_theme_configured() -> None:
    """Without a Theme, `{% theme_html_attrs %}` still emits
    `data-theme="system"` so the `[data-theme="dark"]` selectors emitted by
    the CSS fallback can match and the switcher can toggle modes."""
    template = Template("{% load wagtail_themes %}{% theme_html_attrs %}")
    rendered = template.render(Context({}))
    assert 'data-theme="system"' in rendered
    assert 'data-theme-name="default"' in rendered
    assert 'class="theme-default"' in rendered


def test_theme_html_attrs_can_opt_out_of_fallback() -> None:
    template = Template(
        "{% load wagtail_themes %}{% theme_html_attrs fallback=False %}"
    )
    rendered = template.render(Context({}))
    assert rendered.strip() == ""
