"""Wagtail snippet ViewSets for Theme and BrandColor."""

from __future__ import annotations

from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import BrandColor, Theme

PALETTE_ICON = "wagtail-themes-palette"


class ThemeViewSet(SnippetViewSet):
    model = Theme
    icon = PALETTE_ICON
    menu_label = "Themes"
    menu_name = "themes"
    add_to_admin_menu = False
    list_display = ["name", "slug", "default_mode", "is_default", "updated_at"]
    list_filter = ["default_mode", "is_default"]
    search_fields = ["name", "slug"]
    ordering = ["name"]


class BrandColorViewSet(SnippetViewSet):
    model = BrandColor
    icon = "pick"
    menu_label = "Brand Colors"
    menu_name = "brand-colors"
    add_to_admin_menu = False
    list_display = ["name", "theme", "color_preview", "is_active", "sort_order"]
    list_filter = ["theme", "is_active"]
    search_fields = ["name"]
    ordering = ["theme", "sort_order", "name"]


class WagtailThemesViewSetGroup(SnippetViewSetGroup):
    items = [ThemeViewSet, BrandColorViewSet]
    menu_icon = PALETTE_ICON
    menu_label = "Themes"
    menu_name = "wagtail-themes"
    add_to_admin_menu = True
    menu_order = 900
