"""Tests for theme cloning (service + management command) — issue #4."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from wagtail_themes.models import BrandColor, Theme
from wagtail_themes.services import build_clone_instance, clone_theme


@pytest.fixture
def source(db) -> Theme:
    theme = Theme.objects.create(
        name="Marketing",
        slug="marketing",
        is_default=True,
        light_bg="#fafafa",
        radius_md="0.75rem",
        heading_font="Georgia, serif",
    )
    BrandColor.objects.create(theme=theme, name="Primary", color_value="rebeccapurple")
    BrandColor.objects.create(
        theme=theme,
        name="Accent",
        color_value="hsl(217 91% 60%)",
        color_value_dark="#1e3a8a",
        sort_order=1,
    )
    BrandColor.objects.create(
        theme=theme, name="Retired", color_value="#999999", is_active=False
    )
    return theme


@pytest.mark.django_db
def test_clone_copies_token_fields(source: Theme) -> None:
    clone = clone_theme(source)
    assert clone.pk != source.pk
    assert clone.light_bg == "#fafafa"
    assert clone.radius_md == "0.75rem"
    assert clone.heading_font == "Georgia, serif"


@pytest.mark.django_db
def test_clone_is_never_default(source: Theme) -> None:
    clone = clone_theme(source)
    assert clone.is_default is False
    source.refresh_from_db()
    assert source.is_default is True  # original keeps its default flag


@pytest.mark.django_db
def test_clone_default_name_and_slug(source: Theme) -> None:
    clone = clone_theme(source)
    assert clone.name == "Marketing (copy)"
    assert clone.slug == "marketing-copy"


@pytest.mark.django_db
def test_repeated_clones_get_unique_slugs(source: Theme) -> None:
    first = clone_theme(source)
    second = clone_theme(source)
    third = clone_theme(source)
    assert first.slug == "marketing-copy"
    assert second.slug == "marketing-copy-2"
    assert third.slug == "marketing-copy-3"


@pytest.mark.django_db
def test_clone_custom_name_and_slug(source: Theme) -> None:
    clone = clone_theme(source, name="Campaign", slug="campaign-2025")
    assert clone.name == "Campaign"
    assert clone.slug == "campaign-2025"


@pytest.mark.django_db
def test_clone_deep_copies_brand_colors_including_inactive(source: Theme) -> None:
    clone = clone_theme(source)
    colors = {bc.name: bc for bc in clone.brand_colors.all()}
    assert set(colors) == {"Primary", "Accent", "Retired"}
    # values preserved verbatim (named + hsl + dark override + inactive flag)
    assert colors["Primary"].color_value == "rebeccapurple"
    assert colors["Accent"].color_value == "hsl(217 91% 60%)"
    assert colors["Accent"].color_value_dark == "#1e3a8a"
    assert colors["Accent"].sort_order == 1
    assert colors["Retired"].is_active is False
    # copies are distinct rows on the new theme, not the source's
    assert all(bc.theme_id == clone.pk for bc in clone.brand_colors.all())
    assert source.brand_colors.count() == 3


@pytest.mark.django_db
def test_build_clone_instance_is_unsaved(source: Theme) -> None:
    instance = build_clone_instance(source)
    assert instance.pk is None
    assert instance.is_default is False


@pytest.mark.django_db
def test_management_command_clones(source: Theme) -> None:
    call_command("wagtail_themes_clone_theme", "marketing", "--slug", "marketing-b")
    clone = Theme.objects.get(slug="marketing-b")
    assert clone.brand_colors.count() == 3


@pytest.mark.django_db
def test_management_command_errors_on_missing_source(db) -> None:
    with pytest.raises(CommandError):
        call_command("wagtail_themes_clone_theme", "does-not-exist")


def _theme_form_data(theme: Theme) -> dict:
    """Serialise a Theme's field values into admin-form POST data."""
    data: dict = {}
    for field in Theme._meta.concrete_fields:
        if field.name in {"id", "created_at", "updated_at"}:
            continue
        value = getattr(theme, field.name)
        if isinstance(value, bool):
            if value:
                data[field.name] = "on"  # unchecked checkboxes are omitted
        else:
            data[field.name] = "" if value is None else str(value)
    return data


@pytest.mark.django_db
def test_admin_copy_flow_clones_brand_colors(client, django_user_model, source):
    """The copy view → add view session handoff copies brand colors in the admin."""
    admin = django_user_model.objects.create_superuser("boss", "b@x.com", "pw")
    client.force_login(admin)

    # GET the copy view: pre-fills the form and records the source in the session.
    copy_resp = client.get(f"/admin/snippets/wagtail_themes/theme/copy/{source.pk}/")
    assert copy_resp.status_code == 200

    # POST the (pre-filled) form to the add view, which handles copy submissions.
    from wagtail_themes.services import build_clone_instance

    payload = _theme_form_data(build_clone_instance(source))
    add_resp = client.post("/admin/snippets/wagtail_themes/theme/add/", payload)
    assert add_resp.status_code == 302

    clone = Theme.objects.get(slug="marketing-copy")
    assert clone.is_default is False
    assert clone.brand_colors.count() == 3


@pytest.mark.django_db
def test_plain_add_does_not_clone_brand_colors(client, django_user_model, source):
    """A normal 'Add theme' (no copy) must not carry a stale copy source."""
    admin = django_user_model.objects.create_superuser("boss", "b@x.com", "pw")
    client.force_login(admin)

    # Prime the session with a copy source, then visit the plain add page (GET),
    # which should clear it, so the subsequent create has no brand colors.
    client.get(f"/admin/snippets/wagtail_themes/theme/copy/{source.pk}/")
    client.get("/admin/snippets/wagtail_themes/theme/add/")

    payload = {"name": "Fresh", "slug": "fresh", "default_mode": "system"}
    # Fill remaining required fields from a blank instance's defaults.
    payload.update(
        {k: v for k, v in _theme_form_data(Theme()).items() if k not in payload}
    )
    add_resp = client.post("/admin/snippets/wagtail_themes/theme/add/", payload)
    assert add_resp.status_code == 302

    fresh = Theme.objects.get(slug="fresh")
    assert fresh.brand_colors.count() == 0
