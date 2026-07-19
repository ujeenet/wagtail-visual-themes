"""Tests for the starter theme presets (issue #7)."""

import pytest
from django.core.management import call_command

from wagtail_themes.models import BrandColor, Theme
from wagtail_themes.presets import PRESETS, load_presets


@pytest.mark.django_db
def test_load_presets_creates_all() -> None:
    themes = load_presets()
    assert len(themes) == len(PRESETS)
    assert set(Theme.objects.values_list("slug", flat=True)) == {
        p["slug"] for p in PRESETS
    }


@pytest.mark.django_db
def test_presets_are_never_default() -> None:
    load_presets()
    assert not Theme.objects.filter(is_default=True).exists()


@pytest.mark.django_db
def test_load_presets_is_idempotent() -> None:
    load_presets()
    load_presets()
    assert Theme.objects.count() == len(PRESETS)
    # brand colors not duplicated on a second run
    total_expected = sum(len(p["brand_colors"]) for p in PRESETS)
    assert BrandColor.objects.count() == total_expected


@pytest.mark.django_db
def test_load_presets_does_not_clobber_edits_without_reset() -> None:
    load_presets()
    slate = Theme.objects.get(slug="slate")
    slate.light_bg = "#123456"
    slate.save()

    load_presets()  # no reset
    slate.refresh_from_db()
    assert slate.light_bg == "#123456"


@pytest.mark.django_db
def test_reset_restores_preset_values() -> None:
    load_presets()
    slate = Theme.objects.get(slug="slate")
    slate.light_bg = "#123456"
    slate.save()

    load_presets(reset=True)
    slate.refresh_from_db()
    assert slate.light_bg == "#ffffff"  # slate uses the default light bg


@pytest.mark.django_db
def test_reset_preserves_is_default_flag() -> None:
    load_presets()
    slate = Theme.objects.get(slug="slate")
    slate.is_default = True
    slate.save()

    load_presets(reset=True)
    slate.refresh_from_db()
    assert slate.is_default is True


@pytest.mark.django_db
def test_presets_brand_colors_created() -> None:
    load_presets()
    sunset = Theme.objects.get(slug="sunset")
    names = set(sunset.brand_colors.values_list("name", flat=True))
    assert {"Primary", "Accent", "Warm"} <= names


@pytest.mark.django_db
@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p["slug"])
def test_preset_text_passes_aa_in_both_modes(preset) -> None:
    """Primary/secondary text and links must reach WCAG AA (4.5:1) in both modes."""
    load_presets()
    theme = Theme.objects.get(slug=preset["slug"])
    for dark in (False, True):
        report = {r["label"]: r for r in theme.contrast_report(dark=dark)}
        mode = "dark" if dark else "light"
        for label in (
            "Text primary on background",
            "Text secondary on background",
            "Link on background",
        ):
            ratio = report[label]["ratio"]
            assert ratio is not None and ratio >= 4.5, (
                f"{preset['slug']} {mode}: {label} = {ratio}"
            )


@pytest.mark.django_db
def test_management_command_loads_presets() -> None:
    call_command("wagtail_themes_load_presets")
    assert Theme.objects.count() == len(PRESETS)


@pytest.mark.django_db
def test_management_command_reset() -> None:
    load_presets()
    emerald = Theme.objects.get(slug="emerald")
    emerald.brand_colors.all().delete()
    call_command("wagtail_themes_load_presets", "--reset")
    emerald.refresh_from_db()
    assert emerald.brand_colors.count() == 2


@pytest.mark.django_db
def test_all_preset_brand_colors_are_parseable_or_gradient() -> None:
    """Solid preset brand colors must yield an rgb triplet (regression for #6)."""
    from wagtail_themes.color_utils import is_gradient

    load_presets()
    for bc in BrandColor.objects.all():
        if not is_gradient(bc.color_value):
            assert bc.rgb_triplet is not None, f"{bc.name}={bc.color_value}"
