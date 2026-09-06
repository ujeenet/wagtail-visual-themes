# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] — 2026-09-06

### Added

- **Emitted CSS now respects `prefers-reduced-motion`** (#13). `emit_theme_css` appends a `@media (prefers-reduced-motion: reduce)` block that collapses the duration tokens (`--duration-fast`/`-normal`/`-slow`) to `0.01ms` — near-instant, but non-zero so `transitionend`/`animationend` listeners still fire. The block targets the same `selector_root` that declared the tokens, so it wins on source order. Easing tokens (`--ease-*`) are untouched: they describe a curve, not a duration. Consumers that drive their transitions off `var(--duration-*)` get reduced-motion support for free.
- **Tailwind v4 integration guide** (#11). The README's Tailwind section now covers both generations. The v4 story is substantially different — CSS-first `@theme` instead of `tailwind.config.js`, and opacity modifiers compile to `color-mix()`, so the `-rgb` companions and `<alpha-value>` are no longer needed. Documents the same-name vs. `@theme inline` alias patterns (and why `inline` is mandatory for anything that changes per mode), a `@custom-variant` matching the three-state switcher including the system-follows-OS case, and the verified gotchas: `shadow-*` is not runtime-themeable on v4 (use `shadow-[var(--shadow-md)]`), `@theme inline` variables are never emitted to `:root`, and stylesheet order does *not* matter — Tailwind v4 puts its theme variables in `@layer theme` while this package emits unlayered CSS, which outranks any cascade layer regardless of document position. Verified by compiling the documented recipe into a live Wagtail site and checking computed styles in-browser (Tailwind CSS v4.3).

### Changed

- **Packaging metadata reconciled with the actual supported floor** (#14). The trove classifiers claimed Django 5.0/5.1 while `dependencies` said `Django>=4.2` and the floor had moved to Wagtail 7. Classifiers now declare **Django 4.2 and 5.2** — the versions supported across the whole `wagtail>=7.0,<8.0` range — and the CI matrix gained an explicit floor job (Python 3.11 · Wagtail 7.0.x · Django 4.2) plus a pinned Django axis, so the declared support is actually exercised rather than whatever pip happens to resolve.
- **`wagtail` dependency now capped at `<8.0`.** The package is tested and classified for Wagtail 7 only; the open-ended `wagtail>=7.0` would have silently allowed an untested Wagtail 8. The cap will be lifted once 8.x is tested.

## [0.5.1] — 2026-07-19

### Fixed

- **Theme preview no longer crashes for a new or copied (unsaved) theme.** The preview template read the `brand_colors` reverse relation directly, which raises on an instance without a primary key — so the whole preview 500'd while adding a theme, making it look like border/shadow/typography edits "didn't work" in the live preview. Brand colors are now passed through the preview context (guarded by the theme's pk), so the preview renders for unsaved themes and all token edits show live.

### Changed

- **Richer brand-color preview.** The preview now shows each brand color with its full 50→950 shade ramp inline (per color, mode-aware light/dark), with readable shade labels and a clear note for gradients (which have no shade scale). Replaces the previous separate, CSS-variable-driven shades section.

## [0.5.0] — 2026-07-19

### Added

- **Starter theme presets** (#7). A management command `python manage.py wagtail_themes_load_presets` creates five professionally-tuned themes — **Slate**, **Emerald**, **Sunset**, **Midnight** and **High Contrast** — each with its own brand colors, so a fresh install isn't a blank form. Idempotent; pass `--reset` to restore a preset's colors/tokens after edits. Presets are never marked as the default theme, and their primary/secondary text and links are tuned to pass WCAG AA in both light and dark modes (enforced in the test suite). Also exposed as `wagtail_themes.presets.load_presets(*, reset=False)`.

## [0.4.0] — 2026-07-19

### Added

- **Duplicate a theme** (#4). Themes can now be cloned — including all their brand colors — instead of rebuilt from scratch:
  - A **Copy** action in the Themes snippet listing pre-fills the add form with a ready-to-save duplicate (unique name/slug, never the default) and copies the source theme's brand colors on save.
  - A management command `python manage.py wagtail_themes_clone_theme <source-slug> [--slug NEW] [--name NAME]` for scripting and seeding environments.
  - A reusable `wagtail_themes.services.clone_theme(source, *, name=None, slug=None)` API. Repeated clones get de-duplicated `-copy`, `-copy-2`, … names/slugs; inactive brand colors are preserved.

## [0.3.0] — 2026-07-19

### Added

- **WCAG contrast feedback in the theme preview** (#5). The snippet preview now grades key text/background pairs (primary/secondary/muted text on background and surface, plus link on background) against WCAG 2.1 and shows an **AAA / AA / Fail** badge with the exact contrast ratio, per mode (light/dark). New public helpers `color_utils.contrast_ratio(fg, bg)` and `color_utils.wcag_grade(ratio, *, large_text=False)`, and `Theme.contrast_report(*, dark=False)`.

### Fixed

- **Color parsing now understands `hsl()`/`hsla()` and CSS named colors** (#6). Previously `color_utils.parse_rgb_triplet` only handled hex and `rgb()/rgba()`; values like `hsl(217 91% 60%)`, `white`, or `rebeccapurple` silently produced **no `-rgb` companion and no 50→950 shade scale**, quietly breaking Tailwind opacity utilities and shades. These formats now parse to a proper RGB triplet and get the full treatment. Unsupported inputs (e.g. `oklch()`) still degrade gracefully to no `-rgb`/shades rather than erroring.

## [0.2.1] — 2026-04-26

### Changed

- **Minimum Wagtail bumped to 7.0.** The 0.1 generation supported Wagtail 6+, but the 0.2 migration imports `wagtail.models.preview` which is a 7.x-only path. Rather than ship a CI-fragile package, the supported floor is now Wagtail 7. Users on Wagtail 6.x should pin `wagtail-visual-themes<0.2`.
- CI matrix simplified to Python 3.11/3.12/3.13 × Wagtail 7.x.

## [0.2.0] — 2026-04-26

### Added

- **Expanded design token surface** — themes now emit a comprehensive set of CSS variables on top of the existing surface/semantic/brand/typography/radius/shadow groups:
  - Spacing scale: `--space-0`/`-px`/`-1`/…/`-24` (Tailwind-aligned).
  - Modular font-size scale: `--font-size-xs`/`-sm`/`-base`/`-lg`/`-xl`/`-2xl`/`-3xl`/`-4xl`.
  - Line-height tokens: `--leading-tight`/`-normal`/`-relaxed`.
  - Letter-spacing tokens: `--tracking-tight`/`-normal`/`-wide`.
  - Border-width scale: `--border-1`/`-2`/`-4`/`-8`.
  - Z-index scale: `--z-base`/`-dropdown`/`-sticky`/`-fixed`/`-overlay`/`-modal`/`-popover`/`-tooltip`/`-toast`.
  - Transition tokens: `--duration-fast`/`-normal`/`-slow`, `--ease-out`, `--ease-in-out`.
  - State overlay tokens: `--state-hover-overlay`, `--state-active-overlay`, `--state-disabled-opacity`.
- **Brand color shade scale** — every solid `BrandColor` now auto-emits a Tailwind-aligned `-50`/`-100`/…/`-950` shade scale (HSL-based lightness mixing), each with its own `-rgb` companion.
- **Color picker widget** — paired text input + native `<input type="color">` swatch with two-way sync, used on every color field across `Theme` and `BrandColor` admin forms via the new `ColorFieldPanel`.
- **Custom palette icon** for the Themes snippet menu, registered via the `register_icons` Wagtail hook (replaces fallback to no icon, since `palette` is not a built-in Wagtail icon).
- **Permissions** — new custom permission `wagtail_themes.set_active_theme` separate from standard add/change/delete. Gates the page-level `theme` FK and the site-level `ThemeSiteSetting.theme` field via Wagtail's `FieldPanel(permission=...)` API.
- **Group preset command** — `python manage.py wagtail_themes_setup_groups` creates **Theme Editor** (full CRUD + set_active_theme) and **Theme Selector** (view-only + set_active_theme) groups. Idempotent, supports `--reset`.
- **Editor-facing documentation** — `docs/editor-guide.md`: non-technical walkthrough covering creating themes, naming brand colors, light/dark variants, color roles, accessibility, common recipes, permissions and troubleshooting.
- Comprehensive `help_text` on every Theme color field and BrandColor field, surfaced inline in the Wagtail admin.
- Theme preview template extended to showcase the new tokens (shade scales, font scale, spacing visualisation, leading/tracking, transitions).

### Changed

- `{% theme_css %}` and `{% theme_html_attrs %}` now fall back to an in-memory `Theme()` (using model field defaults) when no Theme is configured. This means a fresh install renders fully styled out of the box, instead of producing empty output. Opt out with `fallback=False`.

### Fixed

- `Theme.emit_css()` no longer raises when called on an unsaved instance. Wagtail's snippet preview renders an in-memory Theme built from form data before save; the reverse `brand_colors` lookup is now guarded by `theme.pk`.

### Migrations

- `0002_alter_theme_options` — adds the custom `set_active_theme` permission.
- `0003_alter_brandcolor_color_value_and_more` — refines `help_text` on color fields (no schema change).

## [0.1.0] — 2026-04-26

### Added

- Initial release of `wagtail-visual-themes`.
- `Theme` snippet with surface colors (light + dark), semantic colors, typography, border radii and shadows.
- `BrandColor` snippet attached to a Theme, emitted as `--color-<slug>` CSS variables with auto-computed `-contrast` and `-rgb` companions.
- `ThemedPageMixin` for opting Wagtail Pages into theme inheritance via the page tree.
- Optional `ThemeSiteSetting` (when `wagtail.contrib.settings` is installed).
- `{% theme_css %}`, `{% theme_html_attrs %}`, `{% theme_no_flash %}`, `{% theme_switcher %}` template tags.
- `wagtail_themes.context_processors.active_theme` for global access to the active theme.
- Live preview of themes and brand colors in the Wagtail snippet admin.
- Minimal three-state theme switcher (light / system / dark) with no-flash inline JS.
