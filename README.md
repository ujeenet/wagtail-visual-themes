# wagtail-visual-themes

Reusable visual themes for [Wagtail](https://wagtail.org/) pages — colors, dark/light mode, typography, border radii and shadows. Themes are managed as snippets, rendered as a single `<style>` block of CSS variables, and resolved automatically per page.

> ⚠️ Alpha. The API may change before 1.0.

---

## Table of contents

- [What you get](#what-you-get)
- [Installation](#installation)
- [Quickstart (5 minutes)](#quickstart-5-minutes)
- [Concepts](#concepts)
- [Wiring up your base template](#wiring-up-your-base-template)
- [Attaching themes to pages](#attaching-themes-to-pages)
- [Theme switcher](#theme-switcher)
- [Using the CSS variables](#using-the-css-variables)
- [Tailwind integration](#tailwind-integration)
- [Brand colors](#brand-colors)
- [Theme resolution rules](#theme-resolution-rules)
- [Template tag reference](#template-tag-reference)
- [Python API reference](#python-api-reference)
- [Recipes](#recipes)
- [Testing your integration](#testing-your-integration)
- [Troubleshooting / FAQ](#troubleshooting--faq)
- [Development](#development)
- [License](#license)

---

## What you get

| | |
|---|---|
| **Editors** | Create one or more `Theme` snippets in the Wagtail admin. Each theme has its own colors (light + dark), typography, radii, shadows, and a list of named brand colors. Live preview shows them all. |
| **Developers** | Drop `{% theme_css %}` in your `<head>` and consume `var(--color-bg)`, `var(--color-primary)`, `var(--radius-md)`, `var(--shadow-md)` in plain CSS, Tailwind, or anywhere else. |
| **Visitors** | Toggle between light, dark and system (OS) modes. The choice survives page reloads. No flash of wrong theme on first paint. |

The package is **zero-coupling**: it doesn't know about your tenant model, your CMS structure, or your build pipeline. It just emits CSS variables.

---

## Installation

```bash
pip install wagtail-visual-themes
```

Add to `INSTALLED_APPS` (after `wagtail.snippets`):

```python
INSTALLED_APPS = [
    # …
    "wagtail.snippets",
    "wagtail_themes",
]
```

Add the context processor so `{% theme_css %}` works without arguments:

```python
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [...],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
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

That's it. There are **no required settings**.

---

## Quickstart (5 minutes)

After installing:

**1. Create a theme.** Go to *Snippets → Themes* in the Wagtail admin, click *Add Theme*, fill in a name (e.g. `Default`) and slug (`default`), tick **is_default**, and save. Tweak colors as you like, or accept the defaults.

**2. Add a brand color** (optional). *Snippets → Brand Colors → Add*. Pick the theme you just created, name it `Primary`, give it `#3b82f6`. Save.

**3. Update your base template.**

```django
{# templates/base.html #}
{% load wagtail_themes %}
<!DOCTYPE html>
<html {% theme_html_attrs %}>
<head>
    <meta charset="utf-8">
    {% theme_no_flash %}
    {% theme_css %}
    <link rel="stylesheet" href="{% static 'css/site.css' %}">
</head>
<body>
    <header style="background: var(--color-surface); color: var(--color-text-primary); padding: 1rem;">
        My site
        {% theme_switcher %}
    </header>
    <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

**4. Reload the page.** You should see your theme applied. Click the switcher to toggle light/system/dark — the page rerenders instantly with no flash on reload.

That's the whole minimum integration. Read on for the details.

---

## Concepts

### Theme

A `Theme` is a snippet that holds **all design tokens**. It has:

- **Surface colors** (light and dark): background, surface, text-primary, text-secondary, text-muted, border.
- **Semantic colors**: success, warning, error, info, link, focus-ring (each with optional dark override).
- **Brand colors**: many-to-one — see below.
- **Typography**: heading font stack, body font stack, weights, scale (small/normal/large), optional URL to an external font CSS (e.g. Google Fonts).
- **Radii**: `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full`.
- **Shadows**: `--shadow-sm`, `--shadow-md`, `--shadow-lg`.
- **Default mode**: `light`, `dark`, or `system`. The mode the site lands on for visitors with no saved preference.
- **`is_default` flag**: when set, this theme is used for any page that doesn't otherwise have one. Only one theme can be default at a time — saving a new default automatically clears it on others.

### BrandColor

A `BrandColor` is a *named* color owned by a Theme — `Primary`, `Accent`, `Aurora`, whatever you want. Each BrandColor emits **three** CSS variables:

| Variable | Example | Notes |
|---|---|---|
| `--color-<slug>` | `--color-primary: #3b82f6;` | The raw value as authored. |
| `--color-<slug>-rgb` | `--color-primary-rgb: 59 130 246;` | RGB triplet, **only if** the value is a solid color (not a gradient). Powers Tailwind opacity. |
| `--color-<slug>-contrast` | `--color-primary-contrast: #ffffff;` | Auto-computed via WCAG luminance. Use for text on top of the brand color. |

You can give a brand color a separate dark-mode value:

- `color_value`: light mode — required.
- `color_value_dark`: dark mode — optional. Falls back to the light value when blank.

Gradients are supported (`linear-gradient(...)`, `radial-gradient(...)`) — they just don't get an `-rgb` companion.

### Modes

Three modes, controlled via `data-theme` on `<html>`:

- `data-theme="light"` — light tokens.
- `data-theme="dark"` — dark tokens.
- `data-theme="system"` — light by default, swaps to dark inside `@media (prefers-color-scheme: dark)`.

The **theme** has a `default_mode`. The **visitor** can override it via the switcher; the choice is persisted in `localStorage` under `wagtail-themes:mode`. The `{% theme_no_flash %}` tag reads that key synchronously before paint.

### Resolution

Each request needs to find one Theme to render. The resolver walks this order:

1. The current page's own `theme` (if it inherits from `ThemedPageMixin`).
2. Each ancestor page's theme, walking up to the root.
3. The Wagtail Site's `ThemeSiteSetting.theme` (if `wagtail.contrib.settings` is installed).
4. The `Theme` row with `is_default=True`.
5. Nothing — the tags render empty strings; your CSS still works using its own fallbacks.

---

## Wiring up your base template

The single most important block of your project's HTML, in full:

```django
{% load wagtail_themes static %}
<!DOCTYPE html>
<html {% theme_html_attrs %}>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    {# Read saved mode from localStorage and apply data-theme BEFORE paint. #}
    {% theme_no_flash %}

    {# Render the active theme as <style>…</style> with all CSS variables. #}
    {% theme_css %}

    {# Your own stylesheets — they can already use var(--…) below this point. #}
    <link rel="stylesheet" href="{% static 'css/site.css' %}">

    <title>{% block title %}{{ page.title }}{% endblock %}</title>
</head>
<body>
    {% block body %}{% endblock %}
</body>
</html>
```

`{% theme_html_attrs %}` expands to something like:

```html
data-theme="system" data-theme-name="default" class="theme-default"
```

You can author CSS that targets a specific theme by slug:

```css
.theme-marketing .hero { background: var(--color-primary); }
.theme-blog      .hero { background: var(--color-surface); }
```

### Order matters

Three rules:

1. **`{% theme_no_flash %}` must come before any visible HTML.** Otherwise the visitor's saved mode applies *after* paint, causing a flash. It's a tiny synchronous `<script>` — that's intentional.
2. **`{% theme_css %}` must come before your own `<link rel="stylesheet">`.** The variables need to be defined before any rule references them.
3. **Don't put `{% theme_css %}` in a child template that renders late** (e.g. inside `{% block content %}`). It belongs in `<head>`.

---

## Attaching themes to pages

You have three patterns. Pick whichever fits.

### Pattern A — page mixin (most flexible)

Every editorial page can pick its own theme; child pages inherit unless they override. Best for sites where different sections (marketing, docs, blog) want different looks.

```python
# myapp/models.py
from wagtail.models import Page
from wagtail_themes.models import ThemedPageMixin


class HomePage(ThemedPageMixin, Page):
    # Show the theme picker in the editor's "Promote" tab,
    # or wherever you want.
    promote_panels = Page.promote_panels + ThemedPageMixin.theme_panels


class BlogIndexPage(ThemedPageMixin, Page):
    promote_panels = Page.promote_panels + ThemedPageMixin.theme_panels


class BlogPostPage(ThemedPageMixin, Page):
    promote_panels = Page.promote_panels + ThemedPageMixin.theme_panels
```

Then run `makemigrations` + `migrate`. The page now has a `theme` FK; setting it on `BlogIndexPage` propagates to all `BlogPostPage` children automatically (resolver walks the tree).

### Pattern B — site setting (simplest, one theme per Wagtail Site)

For a one-site, one-look project. Add `wagtail.contrib.settings` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # …
    "wagtail.contrib.settings",
    "wagtail_themes",
]
```

…and the contrib's context processor:

```python
TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "wagtail.contrib.settings.context_processors.settings",
)
```

Editors will now see *Settings → Themes* in the admin where they can pick one theme per site. No code changes to your Page models needed.

### Pattern C — both

You can use both at the same time. Page-level wins; site-level is the fallback when no page in the tree has a theme. This is what the resolver does by default.

### Pattern D — request-time override

If you want to flip themes on certain conditions (preview, A/B test, query string), set `request.active_theme` somewhere — middleware, a view, anywhere — and the resolver will use it. Example:

```python
# middleware.py
from wagtail_themes.models import Theme

class PreviewThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.GET.get("theme"):
            try:
                request.active_theme = Theme.objects.get(slug=request.GET["theme"])
            except Theme.DoesNotExist:
                pass
        return self.get_response(request)
```

---

## Theme switcher

The package ships a minimal three-state switcher (light / system / dark):

```django
{% load wagtail_themes %}
{% theme_switcher %}
```

It writes to `localStorage` under the key `wagtail-themes:mode` and updates `data-theme` on `<html>` instantly.

### Custom switcher

The contract is small. Write your own UI; the only job is to:

1. Read the current state from `<html data-theme>` or `localStorage["wagtail-themes:mode"]`.
2. On user action, set `data-theme="light"|"dark"|"system"` on `<html>` and write the same value to `localStorage`.

A minimal hand-rolled toggle in vanilla JS:

```html
<button id="toggle">🌓</button>
<script>
const KEY = "wagtail-themes:mode";
const root = document.documentElement;
const cycle = { light: "dark", dark: "system", system: "light" };
document.getElementById("toggle").addEventListener("click", () => {
    const next = cycle[localStorage.getItem(KEY) || root.dataset.theme || "system"];
    root.dataset.theme = next;
    localStorage.setItem(KEY, next);
});
</script>
```

Or React/Vue/Svelte — same contract. You don't need to use `{% theme_switcher %}`.

---

## Using the CSS variables

The full set, available on `:root` (light) and overridden under `[data-theme="dark"]`:

### Surface

```css
var(--color-bg)              /* page background */
var(--color-surface)         /* cards, panels */
var(--color-text-primary)
var(--color-text-secondary)
var(--color-text-muted)
var(--color-border)
```

### Semantic

```css
var(--color-success)
var(--color-warning)
var(--color-error)
var(--color-info)
var(--color-link)
var(--color-focus-ring)
```

### Brand

```css
var(--color-<slug>)            /* e.g. var(--color-primary) */
var(--color-<slug>-rgb)        /* RGB triplet, solid colors only */
var(--color-<slug>-contrast)   /* foreground color */
```

### Typography

```css
var(--font-heading)
var(--font-body)
var(--font-weight-heading)
var(--font-weight-body)
var(--font-size-base)          /* in px, controlled by font_scale */
```

### Geometry

```css
var(--radius-sm)
var(--radius-md)
var(--radius-lg)
var(--radius-full)             /* 9999px — for pills/circles */

var(--shadow-sm)
var(--shadow-md)
var(--shadow-lg)
```

### Practical example

```css
body {
    background: var(--color-bg);
    color: var(--color-text-primary);
    font-family: var(--font-body);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-body);
}

h1, h2, h3 {
    font-family: var(--font-heading);
    font-weight: var(--font-weight-heading);
}

.btn-primary {
    background: var(--color-primary);
    color: var(--color-primary-contrast);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: opacity 0.2s;
}

.btn-primary:hover {
    /* Tailwind-style opacity: requires --color-primary-rgb (auto-emitted for solids) */
    background: rgb(var(--color-primary-rgb) / 0.9);
}

.card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
}

a { color: var(--color-link); }
*:focus-visible { outline: 2px solid var(--color-focus-ring); }
```

---

## Tailwind integration

`wagtail-visual-themes` plays cleanly with Tailwind v3+. The trick: tell Tailwind your theme tokens are CSS variables containing RGB triplets.

In `tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:      "rgb(var(--color-bg-rgb) / <alpha-value>)",
        surface: "rgb(var(--color-surface-rgb) / <alpha-value>)",
        border:  "rgb(var(--color-border-rgb) / <alpha-value>)",
        primary: "rgb(var(--color-primary-rgb) / <alpha-value>)",
        success: "rgb(var(--color-success-rgb) / <alpha-value>)",
        // …add the rest of your brand color slugs
      },
      borderRadius: {
        sm:   "var(--radius-sm)",
        DEFAULT: "var(--radius-md)",
        lg:   "var(--radius-lg)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        DEFAULT: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      fontFamily: {
        heading: "var(--font-heading)",
        body:    "var(--font-body)",
      },
    },
  },
  // For dark-mode utilities (`dark:bg-surface`):
  darkMode: ["class", '[data-theme="dark"]', '[data-theme="system"]'],
};
```

You can now write Tailwind that respects the theme:

```html
<button class="bg-primary text-white hover:bg-primary/80 rounded px-4 py-2 shadow">
    Click me
</button>
<div class="bg-surface text-foreground border border-border rounded-lg p-6">
    A card
</div>
```

The `bg-primary/80` syntax requires the `-rgb` companion variables — `wagtail-visual-themes` emits these automatically for every solid color.

---

## Brand colors

### Naming & slugs

Brand color slugs are auto-derived from the name: `Primary` → `primary`, `Aurora Sunrise` → `aurora-sunrise`, `Brand 2025` → `brand-2025`. Pick names that read well in CSS.

Names must be unique within a Theme.

### Solid colors vs gradients

Both work. Solids accept hex (`#3b82f6`, `#fff`), `rgb()`, `rgba()`. Gradients accept any CSS gradient (`linear-gradient(...)`, `radial-gradient(...)`, `conic-gradient(...)`).

| Color type | Gets `-rgb` companion? | Gets `-contrast` companion? |
|---|---|---|
| Solid (hex/rgb) | ✅ | ✅ (computed from luminance) |
| Gradient | ❌ | ✅ (defaults to `#ffffff`) |

For gradient brand colors, set the `color_value_dark` to a different gradient if your light-mode gradient looks bad in dark mode.

### Brand color choosers (for FK fields)

If you have a model with FK fields pointing at `BrandColor`, use `BrandColorChooserPanel` so editors only see colors belonging to the active theme:

```python
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail_themes.models import BrandColor, ThemedPageMixin
from wagtail_themes.panels import BrandColorChooserPanel
from django.db import models


class CampaignPage(ThemedPageMixin, Page):
    accent = models.ForeignKey(
        BrandColor, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    content_panels = Page.content_panels + [
        FieldPanel("theme"),
        BrandColorChooserPanel("accent"),  # filters by theme set above
    ]
```

The panel reads the theme from `instance.theme` (or, if the model *is* a Theme, from `instance` itself) and limits the dropdown.

---

## Theme resolution rules

When `{% theme_css %}` runs, it asks the resolver: "which theme should I render?" The decision tree:

```
Is `active_theme` already in the template context?         → use it
   │ no
   ▼
Is the current page a ThemedPageMixin with a theme set?   → use it
   │ no
   ▼
Walk up the page tree — does any ancestor have a theme?    → use the closest
   │ no
   ▼
Is wagtail.contrib.settings installed?
  Does the matching Wagtail Site have a ThemeSiteSetting?  → use its theme
   │ no
   ▼
Is there a Theme row with is_default=True?                 → use it
   │ no
   ▼
Render nothing (template tags emit empty strings).
```

The context processor (`wagtail_themes.context_processors.active_theme`) does steps 3–5 once per request and stores the result in the context as `active_theme`.

### Forcing a specific theme

Skip resolution by passing the theme explicitly:

```django
{% theme_css theme=my_theme %}
```

Or set `request.active_theme = my_theme` in middleware/a view.

---

## Template tag reference

All tags live under `{% load wagtail_themes %}`.

### `{% theme_css %}`

```django
{% theme_css %}                              {# auto-resolved theme #}
{% theme_css theme=my_theme %}               {# explicit override   #}
{% theme_css include_style_tag=False %}      {# raw CSS body, no <style> #}
{% theme_css include_fonts=False %}          {# don't emit <link> for custom_fonts_css_url #}
```

Renders one `<style>` block (and optionally a `<link>` for custom fonts) containing every CSS variable.

### `{% theme_html_attrs %}`

```django
<html {% theme_html_attrs %}>
```

Outputs `data-theme="<default_mode>" data-theme-name="<slug>" class="theme-<slug>"`. Use this on `<html>` so visitor mode preferences and theme-scoped CSS classes both work.

### `{% theme_no_flash %}`

```django
<head>
    {% theme_no_flash %}
    {% theme_css %}
    …
</head>
```

Inline `<script>` that reads `localStorage["wagtail-themes:mode"]` and applies it to `<html data-theme>` synchronously. Place at the very top of `<head>`.

### `{% theme_switcher %}`

```django
{% theme_switcher %}
```

Built-in three-state toggle (light/system/dark). Pulls in its own CSS and a small JS file. Skip if you're rolling your own.

---

## Python API reference

```python
from wagtail_themes.models import Theme, BrandColor, ThemedPageMixin
from wagtail_themes.resolver import (
    resolve_theme_for_page,
    resolve_theme_for_request,
    resolve_theme_for_site,
)
from wagtail_themes.panels import BrandColorChooserPanel
from wagtail_themes.widgets import BrandColorChooserWidget
from wagtail_themes.constants import ThemeMode, FontWeight, FontScale
```

### `Theme.emit_css(selector_root=":root") -> str`

Returns the full CSS body (no `<style>` wrapper) for this theme. Useful for caching the CSS or generating it offline.

```python
theme = Theme.objects.get(slug="default")
print(theme.emit_css())
```

### `Theme.get_default() -> Theme | None`

Returns the row with `is_default=True`, or `None`.

### `BrandColor.css_var_name -> str`

Read-only — `--color-<slug>`.

### `BrandColor.contrast_color -> str` and `contrast_color_dark`

Read-only `#000000` or `#ffffff` chosen via WCAG luminance.

### `ThemedPageMixin.get_active_theme() -> Theme | None`

Walks the page tree + falls back to site/default. Same logic the template tags use.

### Resolver functions

```python
resolve_theme_for_page(page)        # walks up tree, then site, then default
resolve_theme_for_request(request)  # request.active_theme → site → default
resolve_theme_for_site(site)        # site setting only
```

---

## Recipes

### Cache the emitted CSS

For high-traffic sites, emit theme CSS once per theme version and serve it from cache:

```python
# views.py
from django.core.cache import cache
from django.http import HttpResponse
from wagtail_themes.models import Theme

def theme_css_view(request, slug):
    theme = Theme.objects.get(slug=slug)
    key = f"wagtail-themes:css:{theme.pk}:{theme.updated_at.timestamp()}"
    css = cache.get(key)
    if css is None:
        css = theme.emit_css()
        cache.set(key, css, timeout=60 * 60 * 24)
    return HttpResponse(css, content_type="text/css")
```

Then reference it as a `<link>` instead of inline `<style>`:

```django
<link rel="stylesheet" href="{% url 'theme_css' slug=active_theme.slug %}?v={{ active_theme.updated_at|date:'U' }}">
```

### Dump CSS to a static file at build time

Useful if you ship a static landing page or mobile app:

```python
# scripts/dump_theme_css.py
import django; django.setup()
from pathlib import Path
from wagtail_themes.models import Theme

out = Path("static/css/themes")
out.mkdir(parents=True, exist_ok=True)
for theme in Theme.objects.all():
    (out / f"{theme.slug}.css").write_text(theme.emit_css())
```

### Per-section themes (marketing vs blog)

```python
class MarketingIndexPage(ThemedPageMixin, Page):
    """Set theme=Marketing on this page; all marketing children inherit."""
    promote_panels = Page.promote_panels + ThemedPageMixin.theme_panels


class BlogIndexPage(ThemedPageMixin, Page):
    """Set theme=Blog here; all posts inherit."""
    promote_panels = Page.promote_panels + ThemedPageMixin.theme_panels
```

A `BlogPostPage` deep under `BlogIndexPage` will resolve to the Blog theme without each post needing to set it.

### A "preview theme" for stakeholders

Let editors preview an unpublished theme without affecting visitors:

```python
# middleware.py
from wagtail_themes.models import Theme

class PreviewThemeMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        slug = request.GET.get("preview_theme")
        if slug and request.user.is_staff:
            try:
                request.active_theme = Theme.objects.get(slug=slug)
            except Theme.DoesNotExist:
                pass
        return self.get_response(request)
```

Now `?preview_theme=halloween` overrides the live theme for staff only.

### Customising the default theme on first install

Use a data migration:

```python
# myapp/migrations/0002_seed_theme.py
from django.db import migrations


def seed_theme(apps, schema_editor):
    Theme = apps.get_model("wagtail_themes", "Theme")
    BrandColor = apps.get_model("wagtail_themes", "BrandColor")
    theme, _ = Theme.objects.get_or_create(
        slug="default",
        defaults={"name": "Default", "is_default": True, "default_mode": "system"},
    )
    BrandColor.objects.get_or_create(
        theme=theme, name="Primary", defaults={"color_value": "#3b82f6"}
    )


class Migration(migrations.Migration):
    dependencies = [("wagtail_themes", "0001_initial"), ("myapp", "0001_initial")]
    operations = [migrations.RunPython(seed_theme, migrations.RunPython.noop)]
```

---

## Testing your integration

The package ships its own pytest suite. To test *your* code:

```python
# tests/test_my_pages.py
import pytest
from wagtail_themes.models import Theme
from myapp.models import HomePage


@pytest.mark.django_db
def test_homepage_uses_marketing_theme(rf, root_page):
    marketing = Theme.objects.create(name="Marketing", slug="marketing")
    home = root_page.add_child(
        instance=HomePage(title="Home", slug="home", theme=marketing)
    )
    assert home.get_active_theme() == marketing


@pytest.mark.django_db
def test_homepage_inherits_default_theme(rf, root_page):
    default = Theme.objects.create(name="Default", slug="default", is_default=True)
    home = root_page.add_child(instance=HomePage(title="Home", slug="home"))
    assert home.get_active_theme() == default
```

---

## Troubleshooting / FAQ

**The page renders without a theme — `var(--color-bg)` is undefined.**
The resolver returned `None`. Options:
- Mark a Theme as `is_default=True`.
- Add `wagtail.contrib.settings` and pick a theme in *Settings → Themes*.
- Make your Page model inherit from `ThemedPageMixin` and set the theme on the page.

**Dark mode doesn't switch on click.**
- Check `<html>` actually changes `data-theme`. Open devtools → Elements.
- Verify `localStorage["wagtail-themes:mode"]` is being written. If not, the page is loaded from `file://` (localStorage may be sandboxed) or the switcher's JS hasn't loaded yet.
- Make sure you have `{% theme_no_flash %}` and `{% theme_switcher %}` *both* loaded; the switcher writes the value, the no-flash script reads it on next paint.

**Tailwind opacity (`bg-primary/50`) doesn't work.**
Tailwind needs the RGB triplet form. Use `rgb(var(--color-primary-rgb) / <alpha-value>)` in the config (see [Tailwind integration](#tailwind-integration)). Gradients don't get an `-rgb` companion — that's by design.

**Editors saved a brand color but it doesn't appear in CSS.**
Brand colors with `is_active=False` are skipped. Also confirm the brand color belongs to the active theme — they're scoped per-theme.

**Pages don't see my changes after editing a Theme.**
The CSS is regenerated on each request — no caching by default. If you added the [emit-once cache recipe](#cache-the-emitted-css), bump or invalidate the cache key.

**Custom fonts URL is loaded twice.**
Make sure `{% theme_css %}` appears only once per page. Or pass `include_fonts=False` to it and link the font file yourself.

**Why aren't button styles tokenised (shape, animation)?**
Intentional. v1 only ships pure tokens (colors, radii, shadows, typography). Components (buttons, cards) compose those tokens however your design system wants.

---

## Development

```bash
git clone https://github.com/ujeenet/wagtail-visual-themes.git
cd wagtail-visual-themes
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Tests
PYTHONPATH=src python -m pytest tests/ -v

# Build wheel + sdist
python -m build

# Lint
ruff check src tests
```

PRs welcome. Keep changes tightly scoped to visual styling; component-specific logic (button shape enums, hero patterns, navigation, logos) is out of scope for this package.

---

## Releasing

CI runs on every push and PR via [.github/workflows/ci.yml](.github/workflows/ci.yml). Publishing is automated via [.github/workflows/publish.yml](.github/workflows/publish.yml) — pushing a `v*` tag triggers a build, runs tests, publishes to PyPI, and creates a GitHub Release.

**One-time setup** (PyPI Trusted Publishing — no API tokens needed):

1. Create a PyPI account at https://pypi.org/account/register/.
2. Go to https://pypi.org/manage/account/publishing/ and click *Add a new pending publisher*.
3. Fill in:
   - **PyPI Project Name**: `wagtail-visual-themes`
   - **Owner**: `ujeenet`
   - **Repository name**: `wagtail-visual-themes`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. In the GitHub repo, go to *Settings → Environments → New environment*, name it `pypi`. (You can add manual approval here if you want a gate before each release.)

**Cutting a release:**

```bash
# 1. Bump version in pyproject.toml (e.g. 0.1.0 → 0.1.1)
# 2. Update CHANGELOG.md
git add pyproject.toml CHANGELOG.md
git commit -m "release: v0.1.1"
git push

# 3. Tag and push the tag — this triggers publish.yml:
git tag v0.1.1
git push origin v0.1.1
```

Watch the *Actions* tab. On success, the package is on PyPI and a GitHub Release exists with the wheel + sdist attached.

**Without trusted publishing** (manual): replace the `pypa/gh-action-pypi-publish` step's `id-token: write` permission with a `PYPI_API_TOKEN` secret and pass it via `password: ${{ secrets.PYPI_API_TOKEN }}`. Trusted publishing is strictly better — recommended.

---

## License

MIT — see [LICENSE](./LICENSE).
