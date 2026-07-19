"""Load a set of professionally-tuned starter themes."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from wagtail_themes.presets import load_presets


class Command(BaseCommand):
    help = "Create a set of starter themes (Slate, Emerald, Sunset, …). Idempotent."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite existing preset themes' colors/tokens back to the preset.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        themes = load_presets(reset=options["reset"])
        slugs = ", ".join(t.slug for t in themes)
        self.stdout.write(
            self.style.SUCCESS(f"Loaded {len(themes)} preset theme(s): {slugs}")
        )
