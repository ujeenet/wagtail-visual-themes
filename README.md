# wagtail-themes

Reusable visual themes for [Wagtail](https://wagtail.org/) pages — colors, dark/light mode, typography, border radii and shadows. Themes are managed as snippets, rendered as a single `<style>` block of CSS variables, and resolved automatically per page.

> ⚠️ Alpha. The API may change before 1.0.

## What it does

- Editors create one or more `Theme` snippets in the Wagtail admin.
- Each theme defines its tokens: surface colors (light + dark), semantic colors, brand colors, typography, radii, shadows.
- Pages either inherit from a `ThemedPageMixin` (FK to a Theme) **or** the site picks a default Theme via a `SiteSetting`.
- Drop `{% theme_css %}` in your `<head>` and the active theme's tokens land as CSS custom properties on `:root`. A built-in switcher (light / system / dark) toggles `data-theme` on `<html>`.
- All your CSS (Tailwind, plain CSS, anywhere) just consumes `var(--color-bg)`, `var(--color-primary)`, `var(--radius-md)`, `var(--shadow-md)` etc. Solid colors also get an `-rgb` companion (`--color-primary-rgb: 59 130 246`) so Tailwind opacity modifiers (`bg-primary/50`) work out of the box.

## Installation

```bash
pip install wagtail-themes
```

Add to `INSTALLED_APPS` (after `wagtail.snippets`):

```python
INSTALLED_APPS = [
    # …
    "wagtail.snippets",
    "wagtail_themes",
]
```

Add the context processor (optional but recommended):

```python
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "OPTIONS": {
        "context_processors": [
            # …
            "wagtail_themes.context_processors.active_theme",
        ],
    },
}]
```

Run migrations:

```bash
python manage.py migrate
```

## Usage

### 1. Render the theme in your base template

```django
{% load wagtail_themes %}
<!DOCTYPE html>
<html {% theme_html_attrs %}>
<head>
    {% theme_no_flash %}{# applies saved theme mode before paint #}
    {% theme_css %}
    {# … #}
</head>
<body>
    {# … #}
    {% theme_switcher %}
</body>
</html>
```

### 2. Pick how pages get a theme

**Option A — per-page mixin (recommended for editorial flexibility)**

```python
from wagtail.models import Page
from wagtail_themes.models import ThemedPageMixin

class HomePage(ThemedPageMixin, Page):
    content_panels = Page.content_panels + ThemedPageMixin.theme_panels
```

A page without a theme inherits from its nearest themed ancestor. If nothing matches up the tree, the site setting wins; otherwise the `Theme` marked `is_default=True`.

**Option B — one theme per Wagtail site**

Add `wagtail.contrib.settings` to `INSTALLED_APPS`, then editors pick a theme under **Settings → Themes** in the Wagtail admin.

### 3. Style your components with the variables

```css
.card {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}
.btn-primary {
    background: var(--color-primary);
    color: var(--color-primary-contrast);
}
/* Tailwind-style opacity using the -rgb companion: */
.btn-primary-soft {
    background: rgb(var(--color-primary-rgb) / 0.15);
}
```

## Tokens emitted

| Group | Variable names |
|---|---|
| Surface | `--color-bg`, `--color-surface`, `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-border` |
| Semantic | `--color-success`, `--color-warning`, `--color-error`, `--color-info`, `--color-link`, `--color-focus-ring` |
| Brand | `--color-<slug>` and `--color-<slug>-contrast` for each `BrandColor` |
| Typography | `--font-heading`, `--font-body`, `--font-weight-heading`, `--font-weight-body`, `--font-size-base` |
| Radii | `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full` |
| Shadows | `--shadow-sm`, `--shadow-md`, `--shadow-lg` |

Solid colors additionally get an `-rgb` companion holding the RGB triplet (e.g. `--color-primary-rgb: 59 130 246`) so projects using Tailwind's `<utility>/<opacity>` syntax (or plain `rgb(var(--x) / 0.5)`) work without configuration.

Dark-mode overrides are emitted under `[data-theme="dark"]`, and `[data-theme="system"]` mirrors them inside a `prefers-color-scheme: dark` media query.

## Theme switcher

`{% theme_switcher %}` ships a minimal three-state toggle (light / system / dark). It writes the mode to `localStorage` under `wagtail-themes:mode`; `{% theme_no_flash %}` reads it back synchronously before paint to prevent flash of incorrect theme.

Want a custom switcher? Set `data-theme="light"|"dark"|"system"` on `<html>` yourself — that's the entire contract.

## API reference

### Models

- **`wagtail_themes.models.Theme`** — the snippet. Holds all tokens. `theme.emit_css()` returns the full CSS body.
- **`wagtail_themes.models.BrandColor`** — child snippet, FK to a Theme. Emitted as a `--color-<slug>` variable.
- **`wagtail_themes.models.ThemedPageMixin`** — abstract mixin that adds `theme = FK(Theme, null=True, blank=True)` to a Page subclass. Exposes `get_active_theme()` and `theme_panels`.
- **`wagtail_themes.settings.ThemeSiteSetting`** — opt-in BaseSiteSetting, only registered when `wagtail.contrib.settings` is in `INSTALLED_APPS`.

### Template tags

```django
{% load wagtail_themes %}
{% theme_css %}                              {# <style>…</style> with all tokens #}
{% theme_css theme=my_theme %}               {# override resolution            #}
{% theme_css include_style_tag=False %}      {# raw CSS body                   #}
{% theme_html_attrs %}                       {# data-theme="…" data-theme-name="…" class="theme-…" #}
{% theme_no_flash %}                         {# inline JS to set data-theme before paint #}
{% theme_switcher %}                         {# minimal light/system/dark toggle #}
```

### Resolver

```python
from wagtail_themes.resolver import (
    resolve_theme_for_page,
    resolve_theme_for_request,
    resolve_theme_for_site,
)
```

### Custom panels & widgets

```python
from wagtail_themes.panels import BrandColorChooserPanel
from wagtail_themes.widgets import BrandColorChooserWidget

# Use BrandColorChooserPanel on FKs to BrandColor — it filters the queryset
# down to the active theme automatically and renders swatches in the dropdown.
```

## Development

```bash
# Clone and install in editable mode
git clone https://github.com/ujeenet/wagtail-themes.git
cd wagtail-themes
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the test suite
PYTHONPATH=src python -m pytest tests/ -v
```

## License

MIT — see [LICENSE](./LICENSE).
