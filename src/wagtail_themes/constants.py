"""Token constants exposed to Theme model fields."""

from django.db import models


class ThemeMode(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"
    SYSTEM = "system", "System (follow OS)"


class FontWeight(models.TextChoices):
    LIGHT = "300", "Light (300)"
    REGULAR = "400", "Regular (400)"
    MEDIUM = "500", "Medium (500)"
    SEMIBOLD = "600", "Semibold (600)"
    BOLD = "700", "Bold (700)"
    EXTRABOLD = "800", "Extrabold (800)"


class FontScale(models.TextChoices):
    SMALL = "small", "Small"
    NORMAL = "normal", "Normal"
    LARGE = "large", "Large"


FONT_SCALE_BASE_PX = {
    FontScale.SMALL: 14,
    FontScale.NORMAL: 16,
    FontScale.LARGE: 18,
}


SYSTEM_FONT_STACK = (
    "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Roboto, Oxygen, Ubuntu, Cantarell, sans-serif"
)


DEFAULT_HEADING_FONT = SYSTEM_FONT_STACK
DEFAULT_BODY_FONT = SYSTEM_FONT_STACK
