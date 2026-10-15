import tempfile

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings


class CollectstaticTests(SimpleTestCase):
    """Reproduz o collectstatic do build da imagem: arquivo referenciado e inexistente quebra o deploy."""

    def test_collectstatic_com_manifest(self):
        with tempfile.TemporaryDirectory() as destino, override_settings(
            STATIC_ROOT=destino,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
            },
        ):
            call_command("collectstatic", interactive=False, verbosity=0)
