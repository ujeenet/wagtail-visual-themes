"""Optional `ThemeSiteSetting` — one Theme per Wagtail Site.

This module imports cleanly even when `wagtail.contrib.settings` is not in
INSTALLED_APPS, so consumer projects can pick the page-level pattern only and
ignore site-level. To enable site-level themes, add `wagtail.contrib.settings`
to INSTALLED_APPS.
"""

from __future__ import annotations

from django.apps import apps as django_apps
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting


class ThemeSiteSetting(BaseSiteSetting):
    """Pick the active Theme for a Wagtail Site (admin → Settings → Themes)."""

    theme = models.ForeignKey(
        "wagtail_themes.Theme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The theme to use for pages on this site by default."),
    )

    panels = [FieldPanel("theme")]

    class Meta:
        verbose_name = _("Theme")


if django_apps.is_installed("wagtail.contrib.settings"):
    register_setting(ThemeSiteSetting, icon="palette")
