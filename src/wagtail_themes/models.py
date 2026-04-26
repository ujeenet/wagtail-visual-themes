"""Theme + BrandColor models and the ThemedPageMixin."""

from __future__ import annotations

import re
from typing import Any

from django.db import models
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.models import PreviewableMixin

from .color_utils import best_contrast, is_gradient, parse_rgb_triplet
from .constants import (
    DEFAULT_BODY_FONT,
    DEFAULT_HEADING_FONT,
    FONT_SCALE_BASE_PX,
    FontScale,
    FontWeight,
    ThemeMode,
)


def _slugify_token(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")


class Theme(PreviewableMixin, models.Model):
    """A reusable visual theme — a bag of design tokens emitted as CSS variables.

    Pages opt in by either:
      * inheriting from `ThemedPageMixin` and selecting a `Theme`, or
      * configuring a `ThemeSiteSetting` (one theme per Wagtail Site).
    """

    name = models.CharField(max_length=100, unique=True, help_text=_("Display name."))
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text=_("Used in the wrapping element's class (theme-<slug>)."),
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_("Used when a page has no theme set and no Site setting matches."),
    )

    default_mode = models.CharField(
        max_length=10,
        choices=ThemeMode.choices,
        default=ThemeMode.SYSTEM,
        help_text=_("Initial theme mode when the visitor has no preference saved."),
    )

    light_bg = models.CharField(max_length=64, default="#ffffff")
    light_surface = models.CharField(max_length=64, default="#f8fafc")
    light_text_primary = models.CharField(max_length=64, default="#0f172a")
    light_text_secondary = models.CharField(max_length=64, default="#475569")
    light_text_muted = models.CharField(max_length=64, default="#94a3b8")
    light_border = models.CharField(max_length=64, default="#e2e8f0")

    dark_bg = models.CharField(max_length=64, default="#0f172a")
    dark_surface = models.CharField(max_length=64, default="#1e293b")
    dark_text_primary = models.CharField(max_length=64, default="#f8fafc")
    dark_text_secondary = models.CharField(max_length=64, default="#cbd5e1")
    dark_text_muted = models.CharField(max_length=64, default="#64748b")
    dark_border = models.CharField(max_length=64, default="#334155")

    success_color = models.CharField(max_length=64, default="#16a34a")
    warning_color = models.CharField(max_length=64, default="#f59e0b")
    error_color = models.CharField(max_length=64, default="#dc2626")
    info_color = models.CharField(max_length=64, default="#2563eb")
    link_color = models.CharField(max_length=64, default="#2563eb")
    focus_ring_color = models.CharField(max_length=64, default="#3b82f6")

    success_color_dark = models.CharField(max_length=64, blank=True)
    warning_color_dark = models.CharField(max_length=64, blank=True)
    error_color_dark = models.CharField(max_length=64, blank=True)
    info_color_dark = models.CharField(max_length=64, blank=True)
    link_color_dark = models.CharField(max_length=64, blank=True)
    focus_ring_color_dark = models.CharField(max_length=64, blank=True)

    heading_font = models.CharField(
        max_length=255,
        default=DEFAULT_HEADING_FONT,
        help_text=_("CSS font-family stack for headings."),
    )
    body_font = models.CharField(
        max_length=255,
        default=DEFAULT_BODY_FONT,
        help_text=_("CSS font-family stack for body text."),
    )
    custom_fonts_css_url = models.URLField(
        blank=True,
        help_text=_("Optional URL to a stylesheet (e.g. Google Fonts) to load."),
    )
    heading_font_weight = models.CharField(
        max_length=8, choices=FontWeight.choices, default=FontWeight.BOLD
    )
    body_font_weight = models.CharField(
        max_length=8, choices=FontWeight.choices, default=FontWeight.REGULAR
    )
    font_scale = models.CharField(
        max_length=10, choices=FontScale.choices, default=FontScale.NORMAL
    )

    radius_sm = models.CharField(max_length=32, default="0.25rem")
    radius_md = models.CharField(max_length=32, default="0.5rem")
    radius_lg = models.CharField(max_length=32, default="1rem")
    radius_full = models.CharField(max_length=32, default="9999px")

    shadow_sm = models.CharField(
        max_length=255, default="0 1px 2px 0 rgb(0 0 0 / 0.05)"
    )
    shadow_md = models.CharField(
        max_length=255,
        default="0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    )
    shadow_lg = models.CharField(
        max_length=255,
        default="0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Theme")
        verbose_name_plural = _("Themes")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.is_default:
            type(self)._default_manager.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls) -> "Theme | None":
        return cls._default_manager.filter(is_default=True).first()

    @cached_property
    def font_size_base_px(self) -> int:
        return FONT_SCALE_BASE_PX.get(FontScale(self.font_scale), 16)

    def _semantic_dark(self, light_value: str, dark_value: str) -> str:
        return dark_value or light_value

    def emit_css(self, selector_root: str = ":root") -> str:
        """Return the full <style> body for this theme as a string."""
        from .css_emitter import emit_theme_css

        return emit_theme_css(self, selector_root=selector_root)

    def get_preview_template(self, request: Any, mode_name: str) -> str:
        return "wagtail_themes/preview/theme_preview.html"

    def get_preview_context(self, request: Any, mode_name: str) -> dict[str, Any]:
        return {"theme": self, "preview_mode": mode_name or "light"}

    @classmethod
    def get_preview_modes(cls) -> list[tuple[str, str]]:
        return [
            ("light", _("Light mode")),
            ("dark", _("Dark mode")),
        ]

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("name"), FieldPanel("slug")]),
                FieldRowPanel(
                    [FieldPanel("default_mode"), FieldPanel("is_default")]
                ),
            ],
            heading=_("General"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("light_bg"), FieldPanel("dark_bg")]
                ),
                FieldRowPanel(
                    [FieldPanel("light_surface"), FieldPanel("dark_surface")]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("light_text_primary"),
                        FieldPanel("dark_text_primary"),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("light_text_secondary"),
                        FieldPanel("dark_text_secondary"),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("light_text_muted"),
                        FieldPanel("dark_text_muted"),
                    ]
                ),
                FieldRowPanel(
                    [FieldPanel("light_border"), FieldPanel("dark_border")]
                ),
            ],
            heading=_("Surface colors (light / dark)"),
            classname="collapsible",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("success_color"), FieldPanel("success_color_dark")]
                ),
                FieldRowPanel(
                    [FieldPanel("warning_color"), FieldPanel("warning_color_dark")]
                ),
                FieldRowPanel(
                    [FieldPanel("error_color"), FieldPanel("error_color_dark")]
                ),
                FieldRowPanel(
                    [FieldPanel("info_color"), FieldPanel("info_color_dark")]
                ),
                FieldRowPanel(
                    [FieldPanel("link_color"), FieldPanel("link_color_dark")]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("focus_ring_color"),
                        FieldPanel("focus_ring_color_dark"),
                    ]
                ),
            ],
            heading=_("Semantic colors"),
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("heading_font"),
                FieldPanel("body_font"),
                FieldPanel("custom_fonts_css_url"),
                FieldRowPanel(
                    [
                        FieldPanel("heading_font_weight"),
                        FieldPanel("body_font_weight"),
                    ]
                ),
                FieldPanel("font_scale"),
            ],
            heading=_("Typography"),
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("radius_sm"), FieldPanel("radius_md")]
                ),
                FieldRowPanel(
                    [FieldPanel("radius_lg"), FieldPanel("radius_full")]
                ),
            ],
            heading=_("Border radii"),
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("shadow_sm"),
                FieldPanel("shadow_md"),
                FieldPanel("shadow_lg"),
            ],
            heading=_("Shadows"),
            classname="collapsible collapsed",
        ),
    ]


class BrandColor(PreviewableMixin, models.Model):
    """A named brand color belonging to a Theme.

    Emitted as a `--color-<slug>` CSS variable, with an auto-computed
    `--color-<slug>-contrast` companion suitable for foreground text.
    """

    theme = models.ForeignKey(
        Theme, on_delete=models.CASCADE, related_name="brand_colors"
    )
    name = models.CharField(
        max_length=100, help_text=_("e.g. 'Primary', 'Secondary', 'Accent'")
    )
    color_value = models.CharField(
        max_length=500,
        help_text=_("Hex (#fff), rgb(), rgba(), or a CSS gradient."),
    )
    color_value_dark = models.CharField(
        max_length=500, blank=True, help_text=_("Optional dark-mode override.")
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Brand color")
        verbose_name_plural = _("Brand colors")
        ordering = ["sort_order", "name"]
        unique_together = [("theme", "name")]

    def __str__(self) -> str:
        return self.name

    @property
    def slug(self) -> str:
        return _slugify_token(self.name)

    @property
    def css_var_name(self) -> str:
        return f"--color-{self.slug}"

    @property
    def effective_dark_value(self) -> str:
        return self.color_value_dark or self.color_value

    @property
    def contrast_color(self) -> str:
        if is_gradient(self.color_value):
            return "#ffffff"
        return best_contrast(self.color_value)

    @property
    def contrast_color_dark(self) -> str:
        target = self.effective_dark_value
        if is_gradient(target):
            return "#ffffff"
        return best_contrast(target)

    @property
    def rgb_triplet(self) -> str | None:
        rgb = parse_rgb_triplet(self.color_value)
        return f"{rgb[0]} {rgb[1]} {rgb[2]}" if rgb else None

    @property
    def rgb_triplet_dark(self) -> str | None:
        rgb = parse_rgb_triplet(self.effective_dark_value)
        return f"{rgb[0]} {rgb[1]} {rgb[2]}" if rgb else None

    def color_preview(self) -> str:
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            "background:{};border-radius:3px;border:1px solid #ccc;"
            'vertical-align:middle;"></span>',
            self.color_value,
        )

    color_preview.short_description = _("Color")  # type: ignore[attr-defined]

    def get_preview_template(self, request: Any, mode_name: str) -> str:
        return "wagtail_themes/preview/brand_color_preview.html"

    def get_preview_context(self, request: Any, mode_name: str) -> dict[str, Any]:
        return {"color": self}

    panels = [
        FieldPanel("theme"),
        FieldPanel("name"),
        MultiFieldPanel(
            [FieldPanel("color_value")],
            heading=_("Light mode"),
        ),
        MultiFieldPanel(
            [FieldPanel("color_value_dark")],
            heading=_("Dark mode (optional)"),
            classname="collapsible collapsed",
        ),
        FieldRowPanel([FieldPanel("sort_order"), FieldPanel("is_active")]),
    ]


class ThemedPageMixin(models.Model):
    """Add a `theme` FK to a Wagtail Page subclass.

    The active theme is resolved at render time by walking up the page tree:
    the page's own theme (if set), otherwise the nearest ancestor's, otherwise
    the Site setting (if installed), otherwise the default Theme.
    """

    theme = models.ForeignKey(
        Theme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Leave blank to inherit from an ancestor page."),
    )

    class Meta:
        abstract = True

    def get_active_theme(self) -> "Theme | None":
        from .resolver import resolve_theme_for_page

        return resolve_theme_for_page(self)

    def get_context(self, request: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context(request, *args, **kwargs)  # type: ignore[misc]
        context["active_theme"] = self.get_active_theme()
        return context

    theme_panels = [FieldPanel("theme")]
