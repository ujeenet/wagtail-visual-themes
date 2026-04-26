# Editor's guide to wagtail-themes

This is a hands-on, non-technical guide for site editors. If you're a developer wiring up the package, the project [README](../README.md) is for you.

---

## Table of contents

1. [What a Theme is](#what-a-theme-is)
2. [Creating your first Theme](#creating-your-first-theme)
3. [Setting up brand colors](#setting-up-brand-colors)
4. [Light vs. dark variants — what's required, what's optional](#light-vs-dark-variants)
5. [Surface, semantic, and brand colors — what's the difference?](#color-roles)
6. [Choosing accessible color combinations](#accessibility)
7. [Common recipes](#common-recipes)
8. [Permissions — who can change what](#permissions)
9. [Troubleshooting](#troubleshooting)

---

## What a Theme is

A **Theme** is a single record holding every visual decision for your site:

- **Colors** — page backgrounds, text, borders, your brand palette, plus light and dark variants.
- **Typography** — heading and body fonts, weights, scale.
- **Shape** — border radii, shadows.

Editors create one Theme (often called *Default*), tweak it, and the entire site picks up the changes. Multiple Themes are supported if your site has clearly different sections (marketing vs. blog, etc.) — but most sites only ever need one.

Themes aren't pages and aren't published in the traditional sense. They're **snippets** — small, reusable, site-wide configuration objects.

---

## Creating your first Theme

1. In the Wagtail admin sidebar, click **Themes**.
2. Click **Add Theme** in the top-right.
3. Fill in the **General** panel:
   - **Name** — human-readable, e.g. *Default*. Used only in admin.
   - **Slug** — short identifier, e.g. `default`. Becomes part of the CSS class on `<html>` (`class="theme-default"`), so use kebab-case.
   - **Default mode** — which mode the site uses for visitors who haven't toggled before:
     - **Light** — always light unless visitor explicitly chooses dark.
     - **Dark** — always dark unless visitor explicitly chooses light.
     - **System** — follows the visitor's OS setting. Recommended.
   - **Is default** — tick this on the one Theme that should apply when nothing else matches. (Other Themes can still be used for specific pages or sites.)
4. Skim the colour panels. Defaults are sensible whites/slates for light and navy/slate for dark — usable out of the box.
5. **Save**.
6. Use the **Preview** pane on the right to see the theme rendered with all tokens. Toggle *Light mode* / *Dark mode* in the preview menu.

---

## Setting up brand colors

Brand colors are *named* colors that belong to a Theme — typically Primary, Secondary, Accent, but you can name them anything. Each one becomes a CSS variable like `--color-primary` that designers can use in stylesheets.

### Step-by-step

1. Open your Theme. *(You need to save it once before adding brand colors — they need a Theme to attach to.)*
2. In the sidebar, click **Brand colors → Add Brand color**.
3. Pick the **Theme** the colour belongs to.
4. Give it a **Name** — short and CSS-friendly. Use clean, role-based names:
   - ✅ *Primary*, *Secondary*, *Accent*, *Aurora*, *Sunset*
   - ❌ *MyClient_BrandColor_Final_v3*, *#3b82f6*
5. Pick a **Light-mode value**. Click the swatch to open a colour picker, or paste a hex / rgb / gradient.
6. Optionally, set a **Dark-mode value**. Most colours look fine on either background, but vivid colours sometimes need a slightly desaturated version for dark mode. Leave blank to reuse the light value.
7. Save.

### What happens behind the scenes

When you create a brand colour named *Primary* with value `#3b82f6`, the package emits these CSS variables automatically:

| Variable | Value | What it's for |
|---|---|---|
| `--color-primary` | `#3b82f6` | The raw value. |
| `--color-primary-rgb` | `59 130 246` | RGB triplet for opacity utilities like Tailwind's `bg-primary/50`. |
| `--color-primary-contrast` | `#ffffff` | Best-contrast text colour computed automatically. |
| `--color-primary-50` | very light blue | Tint scale, useful for subtle backgrounds. |
| `--color-primary-100` … `--color-primary-900` | progressively darker | Full Tailwind-style shade scale. |

Your developers can reference these directly in CSS:

```css
.cta { background: var(--color-primary); color: var(--color-primary-contrast); }
.subtle-callout { background: var(--color-primary-50); }
```

### How many brand colors should I have?

Most sites need **2–4**. A common pattern:

| Name | Purpose |
|---|---|
| Primary | Main brand colour. CTAs, active links, focused inputs. |
| Secondary | A complementary colour for secondary actions. |
| Accent | A pop colour for highlights, badges, decorative flourishes. |

Don't over-design. Adding 12 brand colours that nobody uses just makes the admin noisier.

### Naming guidance

- Use the **role**, not the colour itself: *Primary*, not *Blue*. If marketing rebrands to red next year, `--color-primary` still makes sense.
- Match across themes. If you have *Marketing* and *Blog* themes, both should have a *Primary* — that way templates work for both.
- Keep names short. `--color-call-to-action-button-background` is technically valid but painful.

---

## Light vs. dark variants

| Field | Light value | Dark value |
|---|---|---|
| **Surface colors** (bg, surface, text, border) | Required | Required (you fill in both columns) |
| **Semantic colors** (success, warning, error, info, link, focus ring) | Required | **Optional** — leave blank to reuse the light value |
| **Brand colors** | Required | **Optional** — leave blank to reuse the light value |

Why do surface colors require both? Because the contrast trade-offs are completely different in light vs. dark mode — white-on-near-white doesn't work in dark mode, navy-on-white doesn't work in light mode. Semantic and brand colors are more often *fine* across both modes; the dark override is for the cases where they're not.

### When does a brand colour need a dark variant?

- **Yes**, if the light-mode value looks washed out on a dark background. Vivid yellows are a common offender.
- **Yes**, if you want to deepen a colour for dark mode (turning a bright `#3b82f6` into a richer `#1e40af`).
- **No**, for most pure mid-saturation colours — they look fine on either background.

If unsure, leave the dark value blank, switch to dark mode in the preview, and see how it looks.

---

## Color roles

There are three "groups" of colors. Each plays a different role.

### Surface colors (light + dark)

The *backbone* of the page. Six fields per mode:

- **Background** — what the page is "made of". Usually pure white or a very dark navy.
- **Surface** — slightly different from background. Used for cards, panels, anything that should feel "raised".
- **Text primary** — body copy.
- **Text secondary** — captions, metadata.
- **Text muted** — disabled or placeholder text.
- **Border** — dividers, card edges, input outlines.

These are the most important fields. Get these right and the rest follows.

### Semantic colors

State-conveying colors. Each has one job:

- **Success** — confirmations, completed states, valid form fields. Usually green.
- **Warning** — cautions, banners about expiring states. Usually amber/yellow.
- **Error** — destructive actions, validation errors. Usually red.
- **Info** — neutral notifications, tips. Usually blue.
- **Link** — anchor colour. Often the same as Primary brand colour.
- **Focus ring** — outline colour for keyboard focus. **Important for accessibility** — should stand out clearly against any background.

Don't confuse semantic and brand. Even if your brand is red, your **error** colour should still be unambiguously "this is bad" red, separate from the brand red. (Otherwise people will think every brand element is an error.)

### Brand colors

Defined per-Theme as separate records. Use them for *brand-specific* surfaces — your logo's primary hue, a campaign accent, a seasonal palette.

---

## Accessibility

Color is one of the easiest accessibility traps to fall into. A few rules:

- **Body text vs. background must hit 7:1 contrast** for AAA, 4.5:1 for AA. Tools like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) will tell you. Pure-white text on pure-black is overkill but always passes.
- **Focus ring must be clearly visible** against both `--color-bg` and the element it surrounds. A faint blue against light grey is invisible. Brand colors often *don't* make good focus rings unless they're high-contrast.
- **Don't rely on colour alone.** A red border on an invalid form field is fine; a red border *and* an icon *and* a text message is better — colourblind users still get the signal.
- **Test in both modes.** A combination that's fine in light mode can fail in dark.

The package's auto-computed `--color-<name>-contrast` variable picks white or black using WCAG luminance — so `color: var(--color-primary-contrast)` on a `background: var(--color-primary)` element is always readable. Use it.

---

## Common recipes

### "I want my site to be brand-coloured but readable"

1. Set **Primary** to your brand colour.
2. **Don't** change `--color-bg` or `--color-text-primary` — keep those neutral. White-on-brand backgrounds are rarely readable for body copy.
3. Use Primary on CTAs, hovered links, and decorative accents only.

### "I want a coloured hero section"

1. Add a brand colour for the hero (e.g. *Hero*).
2. In your hero CSS:
   ```css
   .hero { background: var(--color-hero); color: var(--color-hero-contrast); }
   ```
3. Or use a gradient — paste a `linear-gradient(...)` directly into the colour value.

### "I want a different palette for one section of the site"

If you have developers helping: ask them to set up `ThemedPageMixin` on the relevant Page model. Then you can pick a different Theme on, e.g., the *Blog Index* page, and every blog post inherits.

If you don't have developer access: stick with one Theme and use brand colors with section-specific names (*Blog Accent*, *Marketing Accent*).

### "I want a temporary holiday theme"

Create a second Theme called *Holiday*. Don't set `is_default`. Either:

- Have a developer wire it to a specific page or site, or
- Ask them to swap `is_default` from *Default* to *Holiday* during the season.

Both are cheap operations.

---

## Permissions

By default, only Wagtail admins can create or change Themes. The package ships two preset groups your admin can apply via:

```
python manage.py wagtail_themes_setup_groups
```

| Group | Can do |
|---|---|
| **Theme Editor** | Full CRUD on Themes and Brand colors. Can change which Theme applies to a page or site. |
| **Theme Selector** | Read-only on Themes and Brand colors. Can change which Theme applies to a page (e.g. for editorial staff who need to assign an existing theme but shouldn't be tweaking the design). |

If neither group fits your workflow, your admin can build custom groups by mixing the underlying permissions:

- `wagtail_themes.add_theme` / `change_theme` / `delete_theme` / `view_theme`
- `wagtail_themes.add_brandcolor` / `change_brandcolor` / `delete_brandcolor` / `view_brandcolor`
- `wagtail_themes.set_active_theme` — separate permission for **picking** which Theme applies to a page or site (without necessarily being able to edit Theme records themselves).

---

## Troubleshooting

**My new color isn't showing up.**
- Did you save the Theme? Did you save the Brand color (separate save, separate snippet)?
- Is the Brand color **active**? Inactive ones are excluded.
- Hard-refresh your browser (Cmd-Shift-R) — the CSS is regenerated on each request, but browser caches sometimes hold on.

**Dark mode looks wrong.**
- Check the dark variant. If you left dark colours blank, the light value is reused — which is sometimes wrong.
- Open the Theme preview, switch to *Dark mode* in the preview menu, and see what's actually happening.

**The site has no styling at all.**
- You probably don't have `is_default` ticked on any Theme. The package now auto-falls-back to in-built defaults, so you should see *something*. If you see nothing, your developer may have used `{% theme_css fallback=False %}` — ask them.

**I can't find the Themes menu in the admin.**
- You don't have permission. Ask an admin to run `wagtail_themes_setup_groups` and add you to the **Theme Editor** group.

**The colour picker looks wrong with a gradient.**
- That's expected. The picker is a swatch helper for solid hex colours. For gradients, ignore the swatch and edit the text input directly.

---

If you're stuck, reach out to your developer team or open an issue at https://github.com/ujeenet/wagtail-visual-themes/issues.
