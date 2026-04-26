"""Render a Theme into a self-contained <style> body."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .color_utils import is_gradient, parse_rgb_triplet
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
    return [
        f"  --font-heading: {theme.heading_font};",
        f"  --font-body: {theme.body_font};",
        f"  --font-weight-heading: {theme.heading_font_weight};",
        f"  --font-weight-body: {theme.body_font_weight};",
        f"  --font-size-base: {base_px}px;",
    ]


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


def emit_theme_css(theme: Theme, selector_root: str = ":root") -> str:
    """Render a theme into the body of a `<style>` block.

    Layout:
      :root { /* light mode + non-color tokens */ }
      [data-theme="dark"] { /* dark overrides */ }
      @media (prefers-color-scheme: dark) {
        [data-theme="system"] { /* same as dark */ }
      }
    """
    brand_colors = list(theme.brand_colors.filter(is_active=True))

    light_lines: list[str] = []
    light_lines.extend(_surface_lines(theme, dark=False))
    light_lines.extend(_semantic_lines(theme, dark=False))
    for color in brand_colors:
        light_lines.extend(_brand_color_lines(color, dark=False))
    light_lines.extend(_typography_lines(theme))
    light_lines.extend(_radius_lines(theme))
    light_lines.extend(_shadow_lines(theme))

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
