"""Admin form widgets for color fields."""

from __future__ import annotations

import re
from typing import Any

from django import forms

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _coerce_hex(value: Any) -> str:
    """Return a #rrggbb string for the native color picker.

    The text field is the source of truth — accepts hex / rgb() / gradient.
    The picker is an aid: it shows #rrggbb when the value looks like a hex,
    otherwise a neutral fallback so the picker still renders.
    """
    if not value:
        return "#000000"
    raw = str(value).strip()
    match = _HEX_RE.match(raw)
    if not match:
        return "#000000"
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    return f"#{digits.lower()}"


class ColorPickerWidget(forms.TextInput):
    """A `<input type=text>` paired with a native `<input type=color>`.

    The text input is the form field's actual value (so non-hex values like
    `rgb()` or gradients are preserved). The swatch is a UX aid that updates
    the text on pick, and follows the text on edit when it parses as hex.
    """

    template_name = "wagtail_themes/widgets/color_picker.html"

    class Media:
        css = {"all": ("wagtail_themes/css/color_picker.css",)}
        js = ("wagtail_themes/js/color_picker.js",)

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        ctx = super().get_context(name, value, attrs)
        ctx["widget"]["swatch_value"] = _coerce_hex(value)
        return ctx


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
