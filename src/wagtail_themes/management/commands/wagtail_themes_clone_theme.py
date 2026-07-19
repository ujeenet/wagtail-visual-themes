"""Clone an existing Theme (with its brand colors) from the command line."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from wagtail_themes.models import Theme
from wagtail_themes.services import clone_theme


class Command(BaseCommand):
    help = "Duplicate a Theme (including its brand colors) into a new Theme."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("source_slug", help="Slug of the theme to clone.")
        parser.add_argument("--slug", help="Slug for the new theme.")
        parser.add_argument("--name", help="Display name for the new theme.")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            source = Theme.objects.get(slug=options["source_slug"])
        except Theme.DoesNotExist as exc:
            raise CommandError(
                f"No theme with slug {options['source_slug']!r}."
            ) from exc

        clone = clone_theme(source, name=options.get("name"), slug=options.get("slug"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Cloned {source.slug!r} → {clone.slug!r} "
                f"({clone.brand_colors.count()} brand color(s))."
            )
        )
