from unittest import mock

from django.db import connection
from django.test import TestCase


class SaudeTests(TestCase):
    def test_ok_sem_login(self):
        resp = self.client.get("/saude/")
        self.assertEqual((resp.status_code, resp.json()), (200, {"status": "ok"}))

    def test_503_se_banco_falhar(self):
        with mock.patch.object(connection, "cursor", side_effect=Exception("disco cheio")):
            resp = self.client.get("/saude/")
        self.assertEqual(resp.status_code, 503)


class SQLiteTests(TestCase):
    def test_pragmas_aplicados(self):
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA busy_timeout")
            self.assertEqual(cursor.fetchone()[0], 5000)
            cursor.execute("PRAGMA foreign_keys")
            self.assertEqual(cursor.fetchone()[0], 1)
