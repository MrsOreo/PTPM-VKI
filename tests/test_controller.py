# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest import mock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from controller import RegistrationController
from database import RegistrationDatabase
from validator import RegistrationValidator

LOGIN = "user_test_01"
PASSWORD = "Пароль123!"
CONFIRM = "Пароль123!"
INVALID_CONFIRM = "ДругоП1!"


class IntegrationRegistrationFlow(unittest.TestCase):
    """
    Интеграционные тесты: контроллер + реальный валидатор + реальная БД
    (SQLite). Пользовательский ввод и отправка данных внешнему серверу
    имитируются тестовыми заглушками (unittest.mock).
    """

    def setUp(self):
        self.database = RegistrationDatabase(":memory:")
        self.validator = RegistrationValidator()
        self.controller = RegistrationController(
            validator=self.validator,
            database=self.database,
            user_interface=mock.Mock(),
            notifier=mock.Mock(),
        )

    def tearDown(self):
        self.database.close()

    def set_user_input(self, login, password, confirm):
        self.controller.user_interface.get_registration_data.return_value = (
            login,
            password,
            confirm,
        )

    def test_integration_valid_registration_is_computed_saved_and_notified(self):
        self.set_user_input(LOGIN, PASSWORD, CONFIRM)

        result = self.controller.register_user()

        self.assertEqual((True, ""), result)
        self.assertEqual(1, self.database.count_records())
        self.assertEqual(
            {"is_authorized": True, "error_message": ""},
            self.database.get_record(LOGIN, PASSWORD, CONFIRM),
        )
        self.controller.notifier.send.assert_called_once_with(
            f"Регистрация пользователя '{LOGIN}' прошла успешно."
        )

    def test_integration_invalid_registration_is_saved_and_notified_with_error(self):
        self.set_user_input(LOGIN, PASSWORD, INVALID_CONFIRM)

        is_authorized, error_message = self.controller.register_user()

        self.assertFalse(is_authorized)
        self.assertIn("не совпадают", error_message)
        self.assertEqual(1, self.database.count_records())
        self.assertEqual(
            {"is_authorized": False, "error_message": error_message},
            self.database.get_record(LOGIN, PASSWORD, INVALID_CONFIRM),
        )
        self.controller.notifier.send.assert_called_once_with(
            f"Регистрация пользователя '{LOGIN}' отклонена: {error_message}"
        )

    def test_integration_duplicate_request_takes_result_from_database(self):
        self.set_user_input(LOGIN, PASSWORD, CONFIRM)
        self.controller.validator = mock.Mock(wraps=RegistrationValidator())

        first_result = self.controller.register_user()
        second_result = self.controller.register_user()

        self.assertEqual(first_result, second_result)
        self.controller.validator.validate.assert_called_once()
        self.assertEqual(1, self.database.count_records())
        self.assertEqual(2, self.controller.notifier.send.call_count)

    def test_integration_deleted_record_is_recomputed_on_next_request(self):
        self.set_user_input(LOGIN, PASSWORD, CONFIRM)
        self.controller.validator = mock.Mock(wraps=RegistrationValidator())

        self.controller.register_user()
        self.assertTrue(self.database.delete_record(LOGIN, PASSWORD, CONFIRM))
        self.controller.register_user()

        self.assertEqual(2, self.controller.validator.validate.call_count)
        self.assertEqual(1, self.database.count_records())

    def test_integration_different_users_get_independent_records(self):
        self.set_user_input(LOGIN, PASSWORD, CONFIRM)
        self.assertEqual((True, ""), self.controller.register_user())

        self.set_user_input(LOGIN, PASSWORD, INVALID_CONFIRM)
        is_authorized, error_message = self.controller.register_user()
        self.assertFalse(is_authorized)
        self.assertIn("не совпадают", error_message)

        self.assertEqual(2, self.database.count_records())
        self.assertEqual(2, self.controller.notifier.send.call_count)


class ControllerWithStubs(unittest.TestCase):
    """Юнит-тесты контроллера, где все зависимости — тестовые заглушки."""

    def setUp(self):
        self.validator = mock.Mock()
        self.validator.validate.return_value = (True, "")
        self.database = mock.Mock()
        self.database.get_record.return_value = None
        self.user_interface = mock.Mock()
        self.user_interface.get_registration_data.return_value = (
            LOGIN,
            PASSWORD,
            CONFIRM,
        )
        self.notifier = mock.Mock()
        self.controller = RegistrationController(
            validator=self.validator,
            database=self.database,
            user_interface=self.user_interface,
            notifier=self.notifier,
        )

    def test_without_record_controller_validates_and_adds_to_database(self):
        result = self.controller.register_user()

        self.assertEqual((True, ""), result)
        self.database.get_record.assert_called_once_with(LOGIN, PASSWORD, CONFIRM)
        self.validator.validate.assert_called_once_with(LOGIN, PASSWORD, CONFIRM)
        self.database.add_record.assert_called_once_with(
            LOGIN, PASSWORD, CONFIRM, True, ""
        )
        self.notifier.send.assert_called_once_with(
            f"Регистрация пользователя '{LOGIN}' прошла успешно."
        )

    def test_with_existing_record_controller_skips_validation_and_add(self):
        self.database.get_record.return_value = {
            "is_authorized": False,
            "error_message": "Логин в черном списке",
        }

        result = self.controller.register_user()

        self.assertEqual((False, "Логин в черном списке"), result)
        self.validator.assert_not_called()
        self.database.add_record.assert_not_called()
        self.notifier.send.assert_called_once_with(
            f"Регистрация пользователя '{LOGIN}' отклонена: Логин в черном списке"
        )


if __name__ == "__main__":
    unittest.main()