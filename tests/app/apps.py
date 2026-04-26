from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = "tests.app"
    label = "tests_app"
    default_auto_field = "django.db.models.BigAutoField"
