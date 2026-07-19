"""Reusable operations on themes, shared by the admin views and CLI commands."""

from __future__ import annotations

from django.db.models import Q

from .models import BrandColor, Theme

# Theme fields that must never be copied verbatim when duplicating.
_NON_CLONED_FIELDS = frozenset(
    {"id", "name", "slug", "is_default", "created_at", "updated_at"}
)


def _unique_name_and_slug(base_name: str, base_slug: str) -> tuple[str, str]:
    """Return a (name, slug) pair free of existing Themes.

    Both `name` and `slug` are unique on Theme, so they're de-duplicated together
    with a shared numeric suffix ("… (2)" / "…-2") to keep the pair consistent.
    """

    def free(name: str, slug: str) -> bool:
        return not Theme.objects.filter(Q(name=name) | Q(slug=slug)).exists()

    if free(base_name, base_slug):
        return base_name, base_slug
    n = 2
    while not free(f"{base_name} ({n})", f"{base_slug}-{n}"):
        n += 1
    return f"{base_name} ({n})", f"{base_slug}-{n}"


def copy_brand_colors(source: Theme, target: Theme) -> int:
    """Deep-copy every brand colour (active and inactive) from source to target."""
    copies = [
        BrandColor(
            theme=target,
            name=bc.name,
            color_value=bc.color_value,
            color_value_dark=bc.color_value_dark,
            sort_order=bc.sort_order,
            is_active=bc.is_active,
        )
        for bc in source.brand_colors.all()
    ]
    BrandColor.objects.bulk_create(copies)
    return len(copies)


def build_clone_instance(
    source: Theme, *, name: str | None = None, slug: str | None = None
) -> Theme:
    """Return an **unsaved** duplicate of `source` with all token fields copied.

    The copy is never the default theme. `name`/`slug` default to
    "<source> (copy)" / "<source-slug>-copy", de-duplicated with a numeric
    suffix so repeated clones never clash. Brand colours are not copied here —
    that needs a saved theme; see `copy_brand_colors` / `clone_theme`.
    """
    from django.utils.text import slugify

    base_name = name or f"{source.name} (copy)"
    base_slug = slugify(slug or f"{source.slug}-copy")
    new_name, new_slug = _unique_name_and_slug(base_name, base_slug)

    clone = Theme(name=new_name, slug=new_slug, is_default=False)
    for field in source._meta.concrete_fields:
        if field.name in _NON_CLONED_FIELDS:
            continue
        setattr(clone, field.name, getattr(source, field.name))
    return clone


def clone_theme(
    source: Theme, *, name: str | None = None, slug: str | None = None
) -> Theme:
    """Create and return a saved duplicate of `source`, including its brand colours.

    All token fields are copied; brand colours (active and inactive) are
    deep-copied onto the new theme. See `build_clone_instance` for the naming
    and default-flag rules.
    """
    clone = build_clone_instance(source, name=name, slug=slug)
    clone.save()
    copy_brand_colors(source, clone)
    return clone
