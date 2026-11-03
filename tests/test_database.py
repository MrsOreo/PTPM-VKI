import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.database import (
    MESSAGE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    DatabaseRepository,
)


class DatabaseRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = DatabaseRepository(":memory:")

    def tearDown(self):
        self.repo.close()

    def test_add_returns_true_and_saves_record(self):
        self.assertTrue(self.repo.add(1, "alice", "Привет, мир!"))

        comment = self.repo.get_by_id(1)
        self.assertIsNotNone(comment)
        self.assertEqual("alice", comment["name"])
        self.assertEqual("Привет, мир!", comment["message"])

    def test_add_duplicate_id_raises_value_error(self):
        self.repo.add(1, "alice", "Первое сообщение")

        with self.assertRaises(ValueError):
            self.repo.add(1, "bob", "Сообщение с тем же ID")

    def test_add_rejects_too_long_name(self):
        with self.assertRaises(ValueError):
            self.repo.add(1, "a" * (NAME_MAX_LENGTH + 1), "Текст")

    def test_add_rejects_too_long_message(self):
        with self.assertRaises(ValueError):
            self.repo.add(1, "alice", "m" * (MESSAGE_MAX_LENGTH + 1))

    def test_add_rejects_invalid_types(self):
        with self.assertRaises(TypeError):
            self.repo.add("1", "alice", "Текст")
        with self.assertRaises(TypeError):
            self.repo.add(1, None, "Текст")

    def test_get_by_id_returns_record(self):
        self.repo.add(42, "bob", "<b>Жирный</b> текст")

        comment = self.repo.get_by_id(42)

        self.assertEqual(
            {"id": 42, "name": "bob", "message": "<b>Жирный</b> текст"},
            comment,
        )

    def test_get_by_id_returns_none_for_missing_record(self):
        self.assertIsNone(self.repo.get_by_id(999))

    def test_get_by_name_returns_all_user_records(self):
        self.repo.add(1, "alice", "Первое")
        self.repo.add(2, "bob", "Чужое")
        self.repo.add(3, "alice", "Второе")

        comments = self.repo.get_by_name("alice")

        self.assertEqual([1, 3], [comment["id"] for comment in comments])
        self.assertEqual(["Первое", "Второе"], [c["message"] for c in comments])

    def test_get_by_name_returns_empty_list_for_unknown_user(self):
        self.assertEqual([], self.repo.get_by_name("nobody"))

    def test_update_changes_existing_message(self):
        self.repo.add(1, "alice", "Старый текст")

        self.assertTrue(self.repo.update(1, "Новый текст"))

        self.assertEqual("Новый текст", self.repo.get_by_id(1)["message"])

    def test_update_missing_id_returns_false(self):
        self.assertFalse(self.repo.update(999, "Новый текст"))

    def test_update_rejects_too_long_message(self):
        self.repo.add(1, "alice", "Текст")

        with self.assertRaises(ValueError):
            self.repo.update(1, "m" * (MESSAGE_MAX_LENGTH + 1))

    def test_delete_removes_existing_record(self):
        self.repo.add(1, "alice", "Удалить меня")

        self.assertTrue(self.repo.delete(1))
        self.assertIsNone(self.repo.get_by_id(1))

    def test_delete_missing_id_returns_false(self):
        self.assertFalse(self.repo.delete(999))


if __name__ == "__main__":
    unittest.main()
