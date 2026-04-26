"""Admin form widgets for color fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django import forms

if TYPE_CHECKING:
    pass


class ColorPreviewSelect(forms.Select):
    """A `<select>` that renders a colored swatch next to each option label."""

    template_name = "wagtail_themes/widgets/color_preview_select.html"

    class Media:
        css = {"all": ("wagtail_themes/css/brand_color_chooser.css",)}
        js = ("wagtail_themes/js/brand_color_chooser.js",)


class BrandColorChooserWidget(forms.Select):
    """A custom `<select>` widget that previews each BrandColor as a swatch.

    Used by `BrandColorChooserPanel` for FK fields pointing at `BrandColor`.
    The queryset is set on the form field by the panel; the widget just
    renders it richly.
    """

    template_name = "wagtail_themes/widgets/brand_color_chooser.html"

    class Media:
        css = {"all": ("wagtail_themes/css/brand_color_chooser.css",)}
        js = ("wagtail_themes/js/brand_color_chooser.js",)

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
        queryset: Any = None,
        allow_empty: bool = True,
        empty_label: str = "—",
    ) -> None:
        self.queryset = queryset
        self.allow_empty = allow_empty
        self.empty_label = empty_label
        super().__init__(attrs=attrs)

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)

        brand_colors: list[dict[str, Any]] = []
        selected_color: dict[str, Any] | None = None

        if self.queryset is not None:
            for color in self.queryset:
                is_selected = bool(value) and str(color.pk) == str(value)
                data = {
                    "id": color.pk,
                    "name": color.name,
                    "color_value": color.color_value,
                    "selected": is_selected,
                }
                brand_colors.append(data)
                if is_selected:
                    selected_color = data

        context["widget"]["brand_colors"] = brand_colors
        context["widget"]["selected_color"] = selected_color
        context["widget"]["allow_empty"] = self.allow_empty
        context["widget"]["empty_label"] = self.empty_label
        return context
