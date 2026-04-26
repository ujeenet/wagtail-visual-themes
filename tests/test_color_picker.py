"""Tests for ColorPickerWidget and ColorFieldPanel."""

import pytest
from django import forms

from wagtail_themes.models import BrandColor, Theme
from wagtail_themes.panels import ColorFieldPanel
from wagtail_themes.widgets import ColorPickerWidget, _coerce_hex


def test_coerce_hex_passthrough_for_long_hex():
    assert _coerce_hex("#3b82f6") == "#3b82f6"


def test_coerce_hex_expands_short_hex():
    assert _coerce_hex("#fff") == "#ffffff"
    assert _coerce_hex("#0AB") == "#00aabb"


def test_coerce_hex_falls_back_for_unparseable():
    assert _coerce_hex("rgb(0, 0, 0)") == "#000000"
    assert _coerce_hex("linear-gradient(red, blue)") == "#000000"
    assert _coerce_hex("") == "#000000"
    assert _coerce_hex(None) == "#000000"


def test_widget_renders_paired_inputs():
    widget = ColorPickerWidget()
    html = widget.render("light_bg", "#3b82f6", attrs={"id": "id_light_bg"})
    assert 'data-wt-color-picker' in html
    assert 'type="color"' in html
    assert 'value="#3b82f6"' in html
    assert 'name="light_bg"' in html
    assert 'data-wt-color-swatch' in html
    assert 'data-wt-color-text' in html


def test_widget_swatch_falls_back_for_gradient():
    widget = ColorPickerWidget()
    html = widget.render(
        "color_value",
        "linear-gradient(90deg, red, blue)",
        attrs={"id": "id_color_value"},
    )
    # Text input keeps the gradient verbatim …
    assert "linear-gradient(90deg, red, blue)" in html
    # … swatch falls back to neutral so the picker still renders.
    assert 'value="#000000"' in html


def test_widget_media_includes_css_and_js():
    media = ColorPickerWidget().media
    assert "wagtail_themes/css/color_picker.css" in str(media)
    assert "wagtail_themes/js/color_picker.js" in str(media)


def test_color_field_panel_uses_color_picker_widget():
    panel = ColorFieldPanel("light_bg")
    assert panel.widget is ColorPickerWidget


def test_color_field_panel_respects_widget_override():
    class CustomWidget(forms.TextInput):
        pass

    panel = ColorFieldPanel("light_bg", widget=CustomWidget)
    assert panel.widget is CustomWidget


@pytest.mark.django_db
def test_theme_panels_attach_color_picker_to_color_fields():
    """The edit form built from Theme.panels mounts ColorPickerWidget on
    every color CharField, and leaves non-color fields alone."""
    from wagtail.admin.panels import ObjectList

    edit_handler = ObjectList(Theme.panels).bind_to_model(Theme)
    form_class = edit_handler.get_form_class()
    form = form_class()

    color_fields = [
        "light_bg", "light_surface", "light_text_primary", "light_text_secondary",
        "light_text_muted", "light_border",
        "dark_bg", "dark_surface", "dark_text_primary", "dark_text_secondary",
        "dark_text_muted", "dark_border",
        "success_color", "warning_color", "error_color", "info_color",
        "link_color", "focus_ring_color",
        "success_color_dark", "warning_color_dark", "error_color_dark",
        "info_color_dark", "link_color_dark", "focus_ring_color_dark",
    ]
    for fname in color_fields:
        assert isinstance(form.fields[fname].widget, ColorPickerWidget), fname

    # Non-color text fields keep their plain TextInput.
    assert type(form.fields["name"].widget) is forms.TextInput
    assert type(form.fields["radius_md"].widget) is forms.TextInput


@pytest.mark.django_db
def test_brand_color_panels_attach_color_picker():
    from wagtail.admin.panels import ObjectList

    edit_handler = ObjectList(BrandColor.panels).bind_to_model(BrandColor)
    form_class = edit_handler.get_form_class()
    form = form_class()
    assert isinstance(form.fields["color_value"].widget, ColorPickerWidget)
    assert isinstance(form.fields["color_value_dark"].widget, ColorPickerWidget)
    assert type(form.fields["name"].widget) is forms.TextInput


@pytest.mark.django_db
def test_color_picker_widget_renders_in_bound_panel_html():
    """End-to-end: the rendered form HTML for a saved Theme contains the
    picker markup for color fields."""
    from wagtail.admin.panels import ObjectList

    theme = Theme.objects.create(name="T", slug="t")
    edit_handler = ObjectList(Theme.panels).bind_to_model(Theme)
    form_class = edit_handler.get_form_class()
    form = form_class(instance=theme)
    bound = edit_handler.get_bound_panel(instance=theme, request=None, form=form)
    html = bound.render_html()

    assert "data-wt-color-picker" in html
    assert 'name="light_bg"' in html
    assert 'name="dark_bg"' in html
    assert 'name="success_color"' in html
