# -*- coding: utf-8 -*-
import os
import sqlite3
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from database import RegistrationDatabase

LOGIN = "user_test_01"
PASSWORD = "Пароль123!"
CONFIRM = "Пароль123!"


class TestRegistrationDatabase(unittest.TestCase):
    def setUp(self):
        self.database = RegistrationDatabase(":memory:")

    def tearDown(self):
        self.database.close()

    def test_add_record_then_get_record_returns_saved_result(self):
        saved = self.database.add_record(LOGIN, PASSWORD, CONFIRM, True, "")
        self.assertEqual({"is_authorized": True, "error_message": ""}, saved)
        fetched = self.database.get_record(LOGIN, PASSWORD, CONFIRM)
        self.assertEqual({"is_authorized": True, "error_message": ""}, fetched)

    def test_invalid_result_is_stored_as_false_with_error_message(self):
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, False, "Ошибка валидации")
        fetched = self.database.get_record(LOGIN, PASSWORD, CONFIRM)
        self.assertEqual(
            {"is_authorized": False, "error_message": "Ошибка валидации"}, fetched
        )

    def test_get_missing_record_returns_none(self):
        self.assertIsNone(self.database.get_record(LOGIN, PASSWORD, CONFIRM))

    def test_get_missing_record_only_when_full_key_differs(self):
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, True, "")
        self.assertIsNone(self.database.get_record(LOGIN, "Другой123!", CONFIRM))

    def test_add_record_with_same_key_overwrites_previous_result(self):
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, False, "Старая ошибка")
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, True, "")
        self.assertEqual(1, self.database.count_records())
        self.assertEqual(
            {"is_authorized": True, "error_message": ""},
            self.database.get_record(LOGIN, PASSWORD, CONFIRM),
        )

    def test_delete_record_returns_true_and_removes_it(self):
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, True, "")
        self.assertTrue(self.database.delete_record(LOGIN, PASSWORD, CONFIRM))
        self.assertIsNone(self.database.get_record(LOGIN, PASSWORD, CONFIRM))
        self.assertEqual(0, self.database.count_records())

    def test_delete_missing_record_returns_false(self):
        self.assertFalse(self.database.delete_record(LOGIN, PASSWORD, CONFIRM))

    def test_count_records_tracks_additions_and_deletions(self):
        self.assertEqual(0, self.database.count_records())
        self.database.add_record(LOGIN, PASSWORD, CONFIRM, True, "")
        self.database.add_record("second_user", "Пароль123!", "Пароль123!", True, "")
        self.assertEqual(2, self.database.count_records())
        self.database.delete_record(LOGIN, PASSWORD, CONFIRM)
        self.assertEqual(1, self.database.count_records())

    def test_close_makes_connection_inoperable(self):
        self.database.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            self.database.delete_record(LOGIN, PASSWORD, CONFIRM)


if __name__ == "__main__":
    unittest.main()