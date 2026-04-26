"""Custom Wagtail panels for theme-related fields."""

from __future__ import annotations

from typing import Any

from wagtail.admin.panels import FieldPanel

from .widgets import BrandColorChooserWidget


class BrandColorChooserPanel(FieldPanel):
    """A FieldPanel for FK fields to BrandColor that filters by Theme.

    Use on a model that has both a FK to Theme (e.g. via a `theme` attribute,
    or because the model itself *is* the Theme), and one or more FKs to
    BrandColor that should only offer colors belonging to that theme.

    Example:
        class FancyTheme(Theme):
            primary = models.ForeignKey(BrandColor, ...)
            panels = Theme.panels + [BrandColorChooserPanel("primary")]
    """

    def __init__(
        self,
        field_name: str,
        allow_empty: bool = True,
        empty_label: str = "—",
        **kwargs: Any,
    ) -> None:
        self.allow_empty = allow_empty
        self.empty_label = empty_label
        super().__init__(field_name, **kwargs)

    def clone_kwargs(self) -> dict[str, Any]:
        kwargs = super().clone_kwargs()
        kwargs["allow_empty"] = self.allow_empty
        kwargs["empty_label"] = self.empty_label
        return kwargs

    class BoundPanel(FieldPanel.BoundPanel):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)

            if not self.form or self.field_name not in self.form.fields:
                return

            from .models import BrandColor, Theme

            field = self.form.fields[self.field_name]
            theme = self._get_theme()

            if theme is not None and theme.pk:
                queryset = BrandColor.objects.filter(theme=theme, is_active=True)
            else:
                queryset = BrandColor.objects.none()

            field.queryset = queryset
            field.widget = BrandColorChooserWidget(
                queryset=queryset,
                allow_empty=self.panel.allow_empty,
                empty_label=self.panel.empty_label,
            )

        def _get_theme(self):
            from .models import Theme

            instance = self.instance
            if isinstance(instance, Theme):
                return instance if instance.pk else None
            theme = getattr(instance, "theme", None)
            if theme is not None:
                return theme
            return None
