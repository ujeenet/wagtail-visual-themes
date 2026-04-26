"""Render a Theme into a self-contained <style> body."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .color_utils import derive_shades, is_gradient, parse_rgb_triplet
from .constants import FONT_SCALE_BASE_PX, FontScale

if TYPE_CHECKING:
    from .models import BrandColor, Theme


def _color_pair(name: str, value: str) -> list[str]:
    """Emit both `--name` (raw) and `--name-rgb` (space-separated) when possible.

    The `-rgb` triplet form is what enables Tailwind-style opacity modifiers
    like `bg-primary/50` in consuming projects.
    """
    lines = [f"  --{name}: {value};"]
    if not is_gradient(value):
        rgb = parse_rgb_triplet(value)
        if rgb is not None:
            lines.append(f"  --{name}-rgb: {rgb[0]} {rgb[1]} {rgb[2]};")
    return lines


def _brand_color_lines(color: BrandColor, *, dark: bool) -> list[str]:
    value = color.effective_dark_value if dark else color.color_value
    contrast = color.contrast_color_dark if dark else color.contrast_color
    lines = _color_pair(f"color-{color.slug}", value)
    lines.append(f"  --color-{color.slug}-contrast: {contrast};")
    # Tailwind-aligned 50→950 shades, derived via HSL lightness mixing.
    # Gradients return an empty dict so we just skip them silently.
    for shade, shade_value in derive_shades(value).items():
        lines.extend(_color_pair(f"color-{color.slug}-{shade}", shade_value))
    return lines


def _semantic_lines(theme: Theme, *, dark: bool) -> list[str]:
    """Light + dark semantic colors. Falls back to light value if dark blank."""
    pairs: list[tuple[str, str]] = []

    def pair(name: str, light: str, dark_value: str) -> None:
        value = (dark_value or light) if dark else light
        pairs.append((name, value))

    pair("color-success", theme.success_color, theme.success_color_dark)
    pair("color-warning", theme.warning_color, theme.warning_color_dark)
    pair("color-error", theme.error_color, theme.error_color_dark)
    pair("color-info", theme.info_color, theme.info_color_dark)
    pair("color-link", theme.link_color, theme.link_color_dark)
    pair("color-focus-ring", theme.focus_ring_color, theme.focus_ring_color_dark)

    out: list[str] = []
    for name, value in pairs:
        out.extend(_color_pair(name, value))
    return out


def _surface_lines(theme: Theme, *, dark: bool) -> list[str]:
    if dark:
        mapping = {
            "color-bg": theme.dark_bg,
            "color-surface": theme.dark_surface,
            "color-text-primary": theme.dark_text_primary,
            "color-text-secondary": theme.dark_text_secondary,
            "color-text-muted": theme.dark_text_muted,
            "color-border": theme.dark_border,
        }
    else:
        mapping = {
            "color-bg": theme.light_bg,
            "color-surface": theme.light_surface,
            "color-text-primary": theme.light_text_primary,
            "color-text-secondary": theme.light_text_secondary,
            "color-text-muted": theme.light_text_muted,
            "color-border": theme.light_border,
        }
    out: list[str] = []
    for name, value in mapping.items():
        out.extend(_color_pair(name, value))
    return out


def _typography_lines(theme: Theme) -> list[str]:
    base_px = FONT_SCALE_BASE_PX.get(FontScale(theme.font_scale), 16)
    # Tailwind-aligned modular scale, anchored to --font-size-base.
    # Ratios are roughly 1.25x; xs and sm step down, lg through 4xl step up.
    scale_ratios = {
        "xs": 0.75,
        "sm": 0.875,
        "base": 1.0,
        "lg": 1.125,
        "xl": 1.25,
        "2xl": 1.5,
        "3xl": 1.875,
        "4xl": 2.25,
    }
    lines = [
        f"  --font-heading: {theme.heading_font};",
        f"  --font-body: {theme.body_font};",
        f"  --font-weight-heading: {theme.heading_font_weight};",
        f"  --font-weight-body: {theme.body_font_weight};",
        f"  --font-size-base: {base_px}px;",
    ]
    for name, ratio in scale_ratios.items():
        # Round to 3 decimals to keep emitted CSS terse.
        size_rem = round(ratio, 3)
        lines.append(f"  --font-size-{name}: {size_rem}rem;")
    # Line height + letter spacing (fixed scales — uniform across themes).
    lines.extend(
        [
            "  --leading-tight: 1.25;",
            "  --leading-normal: 1.5;",
            "  --leading-relaxed: 1.75;",
            "  --tracking-tight: -0.025em;",
            "  --tracking-normal: 0em;",
            "  --tracking-wide: 0.05em;",
        ]
    )
    return lines


def _radius_lines(theme: Theme) -> list[str]:
    return [
        f"  --radius-sm: {theme.radius_sm};",
        f"  --radius-md: {theme.radius_md};",
        f"  --radius-lg: {theme.radius_lg};",
        f"  --radius-full: {theme.radius_full};",
    ]


def _shadow_lines(theme: Theme) -> list[str]:
    return [
        f"  --shadow-sm: {theme.shadow_sm};",
        f"  --shadow-md: {theme.shadow_md};",
        f"  --shadow-lg: {theme.shadow_lg};",
    ]


# Spacing, border, z-index, transitions and state overlays use fixed
# Tailwind-aligned values. They're not configurable per-theme — editors
# don't typically tweak these, and a coherent scale is more important than
# flexibility. Authors who need different values can override via their
# own CSS after `{% theme_css %}`.

_SPACING_SCALE = {
    "0": "0",
    "px": "1px",
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "8": "2rem",
    "10": "2.5rem",
    "12": "3rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem",
}


def _spacing_lines(_theme: Theme) -> list[str]:
    return [f"  --space-{k}: {v};" for k, v in _SPACING_SCALE.items()]


def _border_width_lines(_theme: Theme) -> list[str]:
    return [
        "  --border-1: 1px;",
        "  --border-2: 2px;",
        "  --border-4: 4px;",
        "  --border-8: 8px;",
    ]


def _z_index_lines(_theme: Theme) -> list[str]:
    return [
        "  --z-base: 0;",
        "  --z-dropdown: 10;",
        "  --z-sticky: 20;",
        "  --z-fixed: 30;",
        "  --z-overlay: 40;",
        "  --z-modal: 50;",
        "  --z-popover: 60;",
        "  --z-tooltip: 70;",
        "  --z-toast: 80;",
    ]


def _transition_lines(_theme: Theme) -> list[str]:
    return [
        "  --duration-fast: 150ms;",
        "  --duration-normal: 200ms;",
        "  --duration-slow: 300ms;",
        "  --ease-out: cubic-bezier(0, 0, 0.2, 1);",
        "  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);",
    ]


def _state_overlay_lines(_theme: Theme) -> list[str]:
    """Opacity values used for hover / active / disabled state overlays.

    Use them with `rgb(var(--color-foo-rgb) / var(--state-hover-overlay))` or
    `opacity: var(--state-disabled-opacity)`.
    """
    return [
        "  --state-hover-overlay: 0.08;",
        "  --state-active-overlay: 0.16;",
        "  --state-disabled-opacity: 0.5;",
    ]


def emit_theme_css(theme: Theme, selector_root: str = ":root") -> str:
    """Render a theme into the body of a `<style>` block.

    Layout:
      :root { /* light mode + non-color tokens */ }
      [data-theme="dark"] { /* dark overrides */ }
      @media (prefers-color-scheme: dark) {
        [data-theme="system"] { /* same as dark */ }
      }
    """
    # Reverse relations require a saved instance. In the snippet preview
    # Wagtail renders an in-memory instance built from form data before save,
    # so guard the lookup and emit no brand-color variables in that case.
    brand_colors = (
        list(theme.brand_colors.filter(is_active=True)) if theme.pk else []
    )

    light_lines: list[str] = []
    light_lines.extend(_surface_lines(theme, dark=False))
    light_lines.extend(_semantic_lines(theme, dark=False))
    for color in brand_colors:
        light_lines.extend(_brand_color_lines(color, dark=False))
    light_lines.extend(_typography_lines(theme))
    light_lines.extend(_radius_lines(theme))
    light_lines.extend(_shadow_lines(theme))
    light_lines.extend(_spacing_lines(theme))
    light_lines.extend(_border_width_lines(theme))
    light_lines.extend(_z_index_lines(theme))
    light_lines.extend(_transition_lines(theme))
    light_lines.extend(_state_overlay_lines(theme))

    dark_lines: list[str] = []
    dark_lines.extend(_surface_lines(theme, dark=True))
    dark_lines.extend(_semantic_lines(theme, dark=True))
    for color in brand_colors:
        dark_lines.extend(_brand_color_lines(color, dark=True))

    out = [f"/* wagtail-visual-themes: {theme.name} */"]
    out.append(f"{selector_root} {{")
    out.extend(light_lines)
    out.append("}")

    out.append('[data-theme="dark"] {')
    out.extend(dark_lines)
    out.append("}")

    out.append("@media (prefers-color-scheme: dark) {")
    out.append('  [data-theme="system"] {')
    out.extend(f"  {line}" for line in dark_lines)
    out.append("  }")
    out.append("}")

    return "\n".join(out)
