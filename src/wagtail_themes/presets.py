"""Professionally-tuned starter themes, loadable via a management command.

Each preset is a plain dict: `slug`, `name`, `default_mode`, a `fields` override
map (anything left out uses the model defaults), and a list of
`(name, light_value, dark_value)` brand colors. Presets are never marked as the
default theme — loading them won't touch a site's live default.

Primary and secondary text are tuned to pass WCAG AA against their backgrounds in
both modes (see tests/test_presets.py).
"""

from __future__ import annotations

from typing import Any

from .models import BrandColor, Theme

PRESETS: list[dict[str, Any]] = [
    {
        "slug": "slate",
        "name": "Slate",
        "default_mode": "system",
        "fields": {
            "link_color": "#2563eb",
            "link_color_dark": "#60a5fa",
            "focus_ring_color": "#3b82f6",
            "radius_md": "0.5rem",
        },
        "brand_colors": [
            ("Primary", "#2563eb", "#60a5fa"),
            ("Accent", "#7c3aed", "#a78bfa"),
        ],
    },
    {
        "slug": "emerald",
        "name": "Emerald",
        "default_mode": "system",
        "fields": {
            "link_color": "#047857",
            "link_color_dark": "#34d399",
            "focus_ring_color": "#10b981",
        },
        "brand_colors": [
            ("Primary", "#059669", "#34d399"),
            ("Accent", "#0d9488", "#2dd4bf"),
        ],
    },
    {
        "slug": "sunset",
        "name": "Sunset",
        "default_mode": "light",
        "fields": {
            "light_bg": "#fffbf5",
            "light_surface": "#fff7ed",
            "light_text_primary": "#1c1917",
            "light_text_secondary": "#57534e",
            "light_border": "#fdba74",
            "link_color": "#c2410c",
            "link_color_dark": "#fb923c",
            "radius_lg": "1.25rem",
        },
        "brand_colors": [
            ("Primary", "#ea580c", "#fb923c"),
            ("Accent", "#db2777", "#f472b6"),
            ("Warm", "linear-gradient(135deg, #f59e0b, #db2777)", ""),
        ],
    },
    {
        "slug": "midnight",
        "name": "Midnight",
        "default_mode": "dark",
        "fields": {
            "dark_bg": "#020617",
            "dark_surface": "#0f172a",
            "dark_border": "#1e293b",
            "link_color_dark": "#818cf8",
            "focus_ring_color": "#6366f1",
        },
        "brand_colors": [
            ("Primary", "#6366f1", "#818cf8"),
            ("Accent", "#22d3ee", "#67e8f9"),
        ],
    },
    {
        "slug": "high-contrast",
        "name": "High Contrast",
        "default_mode": "system",
        "fields": {
            "light_bg": "#ffffff",
            "light_surface": "#ffffff",
            "light_text_primary": "#000000",
            "light_text_secondary": "#1a1a1a",
            "light_text_muted": "#404040",
            "light_border": "#000000",
            "dark_bg": "#000000",
            "dark_surface": "#0a0a0a",
            "dark_text_primary": "#ffffff",
            "dark_text_secondary": "#e5e5e5",
            "dark_text_muted": "#a3a3a3",
            "dark_border": "#ffffff",
            "link_color": "#0000ee",
            "link_color_dark": "#ffff00",
            "focus_ring_color": "#0000ee",
            "radius_sm": "0.125rem",
            "radius_md": "0.25rem",
            "radius_lg": "0.375rem",
        },
        "brand_colors": [
            ("Primary", "#0000ee", "#ffff00"),
        ],
    },
]


# Fields that identify the row or are managed elsewhere — never set from a preset.
_UNMANAGED_FIELDS = frozenset({"id", "slug", "is_default", "created_at", "updated_at"})


def _preset_field_values(preset: dict[str, Any]) -> dict[str, Any]:
    """Canonical token values for a preset: model defaults, overlaid with the preset.

    Using every token field (not just the preset's overrides) means `--reset`
    restores a preset fully — including fields the preset leaves at their model
    default that a user may have since edited.
    """
    values: dict[str, Any] = {
        field.name: field.get_default()
        for field in Theme._meta.concrete_fields
        if field.name not in _UNMANAGED_FIELDS
    }
    values["name"] = preset["name"]
    values["default_mode"] = preset["default_mode"]
    values.update(preset["fields"])
    return values


def _apply_brand_colors(theme: Theme, brand_colors: list[tuple[str, str, str]]) -> None:
    for sort_order, (name, value, value_dark) in enumerate(brand_colors):
        BrandColor.objects.update_or_create(
            theme=theme,
            name=name,
            defaults={
                "color_value": value,
                "color_value_dark": value_dark,
                "sort_order": sort_order,
            },
        )


def load_presets(*, reset: bool = False) -> list[Theme]:
    """Create the starter themes. Idempotent.

    Existing themes (matched by slug) are left untouched unless `reset=True`, in
    which case their token fields and brand colors are overwritten to match the
    preset. The `is_default` flag is never changed.
    """
    themes: list[Theme] = []
    for preset in PRESETS:
        defaults = _preset_field_values(preset)

        theme, created = Theme.objects.get_or_create(
            slug=preset["slug"], defaults=defaults
        )
        if created:
            _apply_brand_colors(theme, preset["brand_colors"])
        elif reset:
            for attr, value in defaults.items():
                setattr(theme, attr, value)
            theme.save()
            theme.brand_colors.all().delete()
            _apply_brand_colors(theme, preset["brand_colors"])

        themes.append(theme)
    return themes
