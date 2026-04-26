"""Wagtail admin registrations for the wagtail_themes app."""

from __future__ import annotations

from django.templatetags.static import static
from django.utils.html import format_html
from wagtail import hooks
from wagtail.snippets.models import register_snippet

from .viewsets import WagtailThemesViewSetGroup

register_snippet(WagtailThemesViewSetGroup)


@hooks.register("insert_global_admin_css")
def wagtail_themes_admin_css() -> str:
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_themes/css/admin.css"),
    )
