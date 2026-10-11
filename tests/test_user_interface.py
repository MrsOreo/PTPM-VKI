# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest import mock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from user_interface import ConsoleUserInterface, UserInterface


class TestUserInterface(unittest.TestCase):
    def test_abstract_user_interface_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            UserInterface()

    def test_console_request_asks_for_login_password_and_confirmation(self):
        with mock.patch(
            "builtins.input", side_effect=["user_test_01", "Пароль123!", "Пароль123!"]
        ) as mocked_input:
            result = ConsoleUserInterface().get_registration_data()

        self.assertEqual(
            ("user_test_01", "Пароль123!", "Пароль123!"), result
        )
        self.assertEqual(3, mocked_input.call_count)

    def test_console_interface_passes_values_untouched(self):
        with mock.patch("builtins.input", side_effect=["", "  ", "Пароль123!"]):
            result = ConsoleUserInterface().get_registration_data()
        self.assertEqual(("", "  ", "Пароль123!"), result)


if __name__ == "__main__":
    unittest.main()