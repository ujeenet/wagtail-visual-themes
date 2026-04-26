# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
