"""Concrete Page model for the test suite — exercises ThemedPageMixin."""

from wagtail.models import Page

from wagtail_themes.models import ThemedPageMixin


class ThemedTestPage(ThemedPageMixin, Page):
    """A Page subclass that opts into theme inheritance."""

    content_panels = Page.content_panels + ThemedPageMixin.theme_panels
