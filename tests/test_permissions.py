"""Tests for the custom set_active_theme permission and group presets."""

from io import StringIO

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command


@pytest.mark.django_db
def test_set_active_theme_permission_is_registered():
    """The permission row exists after migrations have run."""
    perm = Permission.objects.get(
        content_type__app_label="wagtail_themes",
        codename="set_active_theme",
    )
    assert perm.name == "Can set the active theme on a page or site"


@pytest.mark.django_db
def test_setup_groups_command_creates_both_groups():
    out = StringIO()
    call_command("wagtail_themes_setup_groups", stdout=out)
    assert Group.objects.filter(name="Theme Editor").exists()
    assert Group.objects.filter(name="Theme Selector").exists()
    output = out.getvalue()
    assert "Theme Editor" in output
    assert "Theme Selector" in output


@pytest.mark.django_db
def test_theme_editor_group_has_full_crud_and_set_active():
    call_command("wagtail_themes_setup_groups", verbosity=0)
    editor = Group.objects.get(name="Theme Editor")
    codenames = set(editor.permissions.values_list("codename", flat=True))
    expected = {
        "view_theme", "add_theme", "change_theme", "delete_theme",
        "set_active_theme",
        "view_brandcolor", "add_brandcolor",
        "change_brandcolor", "delete_brandcolor",
    }
    assert expected.issubset(codenames)


@pytest.mark.django_db
def test_theme_selector_group_is_read_only_plus_set_active():
    call_command("wagtail_themes_setup_groups", verbosity=0)
    selector = Group.objects.get(name="Theme Selector")
    codenames = set(selector.permissions.values_list("codename", flat=True))
    assert codenames == {"view_theme", "view_brandcolor", "set_active_theme"}


@pytest.mark.django_db
def test_setup_groups_is_idempotent():
    call_command("wagtail_themes_setup_groups", verbosity=0)
    editor = Group.objects.get(name="Theme Editor")
    perms_before = set(editor.permissions.values_list("codename", flat=True))

    # Re-run — should not duplicate or remove anything.
    call_command("wagtail_themes_setup_groups", verbosity=0)
    perms_after = set(editor.permissions.values_list("codename", flat=True))
    assert perms_before == perms_after


@pytest.mark.django_db
def test_setup_groups_reset_replaces_drift():
    """--reset replaces permissions, so manually-added perms get cleared."""
    call_command("wagtail_themes_setup_groups", verbosity=0)
    selector = Group.objects.get(name="Theme Selector")

    # Simulate drift: someone added an unrelated perm
    extra = Permission.objects.first()
    selector.permissions.add(extra)
    assert extra in selector.permissions.all()

    call_command("wagtail_themes_setup_groups", "--reset", verbosity=0)
    selector.refresh_from_db()
    codenames = set(selector.permissions.values_list("codename", flat=True))
    assert codenames == {"view_theme", "view_brandcolor", "set_active_theme"}


@pytest.mark.django_db
def test_themed_page_panel_declares_permission():
    """The page-level theme picker is declared with the gate so users
    without `set_active_theme` don't see the field."""
    from wagtail_themes.models import ThemedPageMixin

    panel = ThemedPageMixin.theme_panels[0]
    assert panel.field_name == "theme"
    assert panel.permission == "wagtail_themes.set_active_theme"


@pytest.mark.django_db
def test_user_without_permission_cannot_see_theme_field():
    """Smoke test: a user lacking set_active_theme has the field hidden by
    Wagtail's panel rendering (Wagtail evaluates `permission` per-bound-panel).
    """
    from wagtail.admin.panels import ObjectList

    from tests.app.models import ThemedTestPage

    user = User.objects.create_user("editor", "e@example.com", "pw")
    # User has no perms attached → the theme field should be excluded.

    edit_handler = ObjectList(
        ThemedPageMixin_theme_panels()
    ).bind_to_model(ThemedTestPage)
    form_class = edit_handler.get_form_class()

    page = ThemedTestPage(title="X", slug="x")

    class _Req:
        def __init__(self, u):
            self.user = u

    form = form_class(instance=page)
    bound = edit_handler.get_bound_panel(
        instance=page, request=_Req(user), form=form
    )
    html = bound.render_html()
    assert 'name="theme"' not in html


def ThemedPageMixin_theme_panels():
    from wagtail_themes.models import ThemedPageMixin

    return ThemedPageMixin.theme_panels
