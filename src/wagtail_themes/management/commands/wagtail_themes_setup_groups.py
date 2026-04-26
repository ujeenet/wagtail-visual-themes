"""Management command — create the canonical Theme Editor / Selector groups.

Idempotent: safe to re-run after package updates to reattach permissions.
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

THEME_EDITOR_GROUP = "Theme Editor"
THEME_SELECTOR_GROUP = "Theme Selector"


# Permissions for each preset group, expressed as (app_label, codename).
THEME_EDITOR_PERMS = [
    ("wagtail_themes", "view_theme"),
    ("wagtail_themes", "add_theme"),
    ("wagtail_themes", "change_theme"),
    ("wagtail_themes", "delete_theme"),
    ("wagtail_themes", "set_active_theme"),
    ("wagtail_themes", "view_brandcolor"),
    ("wagtail_themes", "add_brandcolor"),
    ("wagtail_themes", "change_brandcolor"),
    ("wagtail_themes", "delete_brandcolor"),
]

THEME_SELECTOR_PERMS = [
    ("wagtail_themes", "view_theme"),
    ("wagtail_themes", "view_brandcolor"),
    ("wagtail_themes", "set_active_theme"),
]


def _resolve(perm_keys: list[tuple[str, str]]) -> list[Permission]:
    """Resolve (app_label, codename) tuples to Permission rows.

    Misses are usually a sign migrations haven't run; raise loudly.
    """
    out: list[Permission] = []
    for app_label, codename in perm_keys:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=codename.split("_", 1)[1])
        except ContentType.DoesNotExist:
            ct = None
        try:
            perm = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        except Permission.DoesNotExist as exc:
            hint = (
                "Run `python manage.py migrate wagtail_themes` first."
                if ct is None
                else "The package may have been upgraded — try migrate again."
            )
            raise CommandError(
                f"Permission {app_label}.{codename} not found. {hint}"
            ) from exc
        out.append(perm)
    return out


class Command(BaseCommand):
    help = (
        "Create canonical Wagtail groups for theme management:\n"
        f"  '{THEME_EDITOR_GROUP}'   — full CRUD on Theme/BrandColor + can set on pages.\n"
        f"  '{THEME_SELECTOR_GROUP}' — view-only on Theme/BrandColor + can set on pages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Replace existing permissions on the groups instead of merging. "
                "Won't delete the groups themselves."
            ),
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        editor_perms = _resolve(THEME_EDITOR_PERMS)
        selector_perms = _resolve(THEME_SELECTOR_PERMS)

        editor, editor_created = Group.objects.get_or_create(name=THEME_EDITOR_GROUP)
        if reset:
            editor.permissions.set(editor_perms)
        else:
            editor.permissions.add(*editor_perms)

        selector, selector_created = Group.objects.get_or_create(name=THEME_SELECTOR_GROUP)
        if reset:
            selector.permissions.set(selector_perms)
        else:
            selector.permissions.add(*selector_perms)

        for label, group, created in (
            (THEME_EDITOR_GROUP, editor, editor_created),
            (THEME_SELECTOR_GROUP, selector, selector_created),
        ):
            verb = "created" if created else ("reset" if reset else "updated")
            count = group.permissions.count()
            self.stdout.write(
                self.style.SUCCESS(f"{verb}: {label} ({count} permissions attached)")
            )
