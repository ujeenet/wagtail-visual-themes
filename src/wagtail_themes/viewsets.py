"""Wagtail snippet ViewSets for Theme and BrandColor."""

from __future__ import annotations

from typing import Any

from wagtail.snippets.views.snippets import (
    CopyView,
    CreateView,
    SnippetViewSet,
    SnippetViewSetGroup,
)

from .models import BrandColor, Theme
from .services import build_clone_instance, copy_brand_colors

PALETTE_ICON = "wagtail-themes-palette"

# Session key used to hand the copy source from the copy view (which only
# GETs to pre-fill the form) to the add view (which handles the POST). Wagtail's
# copy form always submits to the add URL, so we can't copy the source's brand
# colours in the copy view itself — we do it once the add view has saved.
_COPY_SOURCE_KEY = "wagtail_themes_copy_source"


class ThemeCopyView(CopyView):
    """Pre-fill the add form with a ready-to-save duplicate of the source theme.

    Resets name/slug (de-duplicated) and clears is_default via
    `build_clone_instance`, and records the source so the add view can copy the
    source's brand colours after saving.
    """

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.session[_COPY_SOURCE_KEY] = self.kwargs.get(self.pk_url_kwarg)
        return super().get(request, *args, **kwargs)

    def get_initial_form_instance(self) -> Theme:
        return build_clone_instance(self.get_object())


class ThemeAddView(CreateView):
    """Add view that also clones brand colours when reached from the copy view."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        # A plain "Add theme" must not carry a stale copy source.
        request.session.pop(_COPY_SOURCE_KEY, None)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: Any) -> Any:
        response = super().form_valid(form)
        source_pk = self.request.session.pop(_COPY_SOURCE_KEY, None)
        if source_pk is not None:
            source = Theme.objects.filter(pk=source_pk).first()
            if source is not None and source.pk != self.object.pk:
                copy_brand_colors(source, self.object)
        return response


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
    copy_view_enabled = True
    add_view_class = ThemeAddView
    copy_view_class = ThemeCopyView


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
