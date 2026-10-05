import hashlib
import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from my_project import BLACKLIST, mask_password, validate_registration

VALID_LOGIN = "user_test_01"
VALID_PASSWORD = "Пароль123!"
VALID_PHONE = "+7-999-123-4567"
VALID_EMAIL = "ivanov@mail.ru"


class TestMaskPassword(unittest.TestCase):
    def test_empty_password_is_masked_as_empty(self):
        self.assertEqual(mask_password(""), "[MASKED:empty]")

    def test_password_is_replaced_with_prefix_of_sha256_hash(self):
        expected = hashlib.sha256(VALID_PASSWORD.encode("utf-8")).hexdigest()[:8]
        self.assertEqual(mask_password(VALID_PASSWORD), f"[MASKED:{expected}]")

    def test_plain_password_is_never_present_in_mask(self):
        self.assertNotIn(VALID_PASSWORD, mask_password(VALID_PASSWORD))

    def test_password_of_non_string_type_is_masked_as_invalid(self):
        self.assertEqual(mask_password(12345), "[MASKED:invalid]")
        self.assertEqual(mask_password(None), "[MASKED:invalid]")


class TestPasswordRules(unittest.TestCase):
    def test_valid_password_is_accepted(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertTrue(is_valid, message)
        self.assertEqual(message, "")

    def test_password_of_exactly_seven_characters_is_accepted(self):
        is_valid, message = validate_registration(VALID_LOGIN, "П1роль!", "П1роль!")
        self.assertTrue(is_valid, message)

    def test_confirmation_differing_from_password_is_rejected(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, VALID_PASSWORD, "ДругойПароль1!"
        )
        self.assertFalse(is_valid, "пароль и подтверждение различаются")
        self.assertIn("не совпадают", message)

    def test_password_shorter_than_seven_characters_is_rejected(self):
        is_valid, message = validate_registration(VALID_LOGIN, "Пар1!", "Пар1!")
        self.assertFalse(is_valid, "пароль короче семи символов")
        self.assertIn("не менее 7", message)

    def test_password_with_latin_letters_is_rejected(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, "Password123!", "Password123!"
        )
        self.assertFalse(is_valid, "латиница в пароле недопустима")
        self.assertIn("недопустимые символы", message)

    def test_password_with_space_is_rejected(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, "Пароль 123!", "Пароль 123!"
        )
        self.assertFalse(is_valid, "пробел в пароле недопустим")
        self.assertIn("недопустимые символы", message)

    def test_password_without_capital_cyrillic_letter_is_rejected(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, "пароль123!", "пароль123!"
        )
        self.assertFalse(is_valid, "нет заглавной буквы")
        self.assertIn("заглавную", message)

    def test_password_without_lowercase_cyrillic_letter_is_rejected(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, "ПАРОЛЬ123!", "ПАРОЛЬ123!"
        )
        self.assertFalse(is_valid, "нет строчной буквы")
        self.assertIn("строчную", message)

    def test_password_without_digit_is_rejected(self):
        is_valid, message = validate_registration(VALID_LOGIN, "Пароль!!!", "Пароль!!!")
        self.assertFalse(is_valid, "нет цифры")
        self.assertIn("цифру", message)

    def test_password_without_special_character_is_rejected(self):
        is_valid, message = validate_registration(VALID_LOGIN, "Пароль123", "Пароль123")
        self.assertFalse(is_valid, "нет спецсимвола")
        self.assertIn("спецсимвол", message)

    def test_confirmation_is_compared_before_other_password_rules(self):
        is_valid, message = validate_registration(VALID_LOGIN, "Пар1!", "Пароль123!")
        self.assertFalse(is_valid, "пароль не проходит две проверки сразу")
        self.assertIn("не совпадают", message)


class TestStringLoginRules(unittest.TestCase):
    def test_string_login_of_minimum_length_is_accepted(self):
        is_valid, message = validate_registration("user_1", VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(is_valid, message)

    def test_string_login_with_digits_and_underscores_is_accepted(self):
        is_valid, message = validate_registration(
            "Ivan_2024", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertTrue(is_valid, message)

    def test_string_login_shorter_than_five_characters_is_rejected(self):
        is_valid, message = validate_registration("user", VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(is_valid, "четыре символа — слишком короткий логин")
        self.assertIn("Неверный формат логина", message)

    def test_string_login_with_hyphen_is_rejected(self):
        is_valid, message = validate_registration(
            "user-01", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "дефис недопустим в логине-строке")
        self.assertIn("Неверный формат логина", message)

    def test_string_login_with_space_is_rejected(self):
        is_valid, message = validate_registration(
            "user name", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "пробел недопустим в логине")
        self.assertIn("Неверный формат логина", message)

    def test_string_login_with_cyrillic_letters_is_rejected(self):
        is_valid, message = validate_registration(
            "пользователь", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "в логине-строке нужна латиница")
        self.assertIn("Неверный формат логина", message)

    def test_string_login_with_trailing_newline_is_rejected(self):
        is_valid, message = validate_registration(
            f"{VALID_LOGIN}\n", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "перевод строки в конце логина недопустим")
        self.assertIn("Неверный формат логина", message)

    def test_empty_login_is_rejected(self):
        is_valid, message = validate_registration("", VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(is_valid, "пустой логин недопустим")
        self.assertIn("Неверный формат логина", message)


class TestPhoneLoginRules(unittest.TestCase):
    def test_phone_login_in_expected_format_is_accepted(self):
        is_valid, message = validate_registration(VALID_PHONE, VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(is_valid, message)

    def test_phone_login_with_short_group_is_rejected(self):
        is_valid, message = validate_registration(
            "+7-99-123-4567", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "в группе после кода страны только две цифры")
        self.assertIn("формат телефона", message)

    def test_phone_login_with_two_digit_country_code_is_rejected(self):
        is_valid, message = validate_registration(
            "+77-999-123-4567", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "код страны должен быть однозначным")
        self.assertIn("формат телефона", message)

    def test_login_starting_with_plus_but_not_a_phone_is_rejected(self):
        is_valid, message = validate_registration(
            "+нетелефон", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "логин с плюсом должен быть телефоном")
        self.assertIn("формат телефона", message)

    def test_phone_login_with_trailing_newline_is_rejected(self):
        is_valid, message = validate_registration(
            f"{VALID_PHONE}\n", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "перевод строки в конце номера недопустим")
        self.assertIn("формат телефона", message)


class TestEmailLoginRules(unittest.TestCase):
    def test_email_login_is_accepted(self):
        is_valid, message = validate_registration(VALID_EMAIL, VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(is_valid, message)

    def test_email_login_with_subdomain_is_accepted(self):
        is_valid, message = validate_registration(
            "ivanov@mail.example.com", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertTrue(is_valid, message)

    def test_email_login_with_plus_tag_is_accepted(self):
        is_valid, message = validate_registration(
            "ivanov+lab@mail.ru", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertTrue(is_valid, message)

    def test_email_login_with_hyphen_at_domain_start_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov@-mail.ru", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "домен не может начинаться с дефиса")
        self.assertIn("формат email", message)

    def test_email_login_with_trailing_dot_in_domain_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov@mail.ru.", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "точка в конце домена недопустима")
        self.assertIn("формат email", message)

    def test_email_login_with_double_dot_in_domain_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov@mail..ru", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "две точки подряд недопустимы")
        self.assertIn("формат email", message)

    def test_email_login_with_dot_before_at_sign_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov.@mail.ru", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "локальная часть не может заканчиваться точкой")
        self.assertIn("формат email", message)

    def test_email_login_with_numeric_domain_suffix_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov@mail.123", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "домен верхнего уровня не может быть числом")
        self.assertIn("формат email", message)

    def test_email_login_without_domain_is_rejected(self):
        is_valid, message = validate_registration(
            "ivanov@mail", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertFalse(is_valid, "адрес без домена недопустим")
        self.assertIn("формат email", message)


class TestBlacklistRules(unittest.TestCase):
    def test_blacklisted_login_is_rejected(self):
        is_valid, message = validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(is_valid, "admin находится в черном списке")
        self.assertIn("черном списке", message)

    def test_blacklisted_login_is_rejected_regardless_of_case(self):
        is_valid, message = validate_registration("AdMiN", VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(is_valid, "регистр не должен обходить черный список")
        self.assertIn("черном списке", message)

    def test_login_containing_blacklisted_word_is_allowed(self):
        is_valid, message = validate_registration(
            "user_admin", VALID_PASSWORD, VALID_PASSWORD
        )
        self.assertTrue(is_valid, "совпадение должно быть полным")

    def test_every_login_from_blacklist_is_rejected(self):
        for login in BLACKLIST:
            with self.subTest(login=login):
                is_valid, _ = validate_registration(
                    login, VALID_PASSWORD, VALID_PASSWORD
                )
                self.assertFalse(is_valid, f"{login} должен отклоняться")


class TestArgumentsTypeValidation(unittest.TestCase):
    def test_non_string_login_is_rejected_with_clear_message(self):
        is_valid, message = validate_registration(None, VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(is_valid, "логин должен быть строкой")
        self.assertIn("должны быть строками", message)

    def test_non_string_password_is_rejected_with_clear_message(self):
        is_valid, message = validate_registration(VALID_LOGIN, 12345, 12345)
        self.assertFalse(is_valid, "пароль должен быть строкой")
        self.assertIn("должны быть строками", message)

    def test_non_string_password_confirmation_is_rejected_with_clear_message(self):
        is_valid, message = validate_registration(
            VALID_LOGIN, VALID_PASSWORD, ["Пароль123!"]
        )
        self.assertFalse(is_valid, "подтверждение должно быть строкой")
        self.assertIn("должны быть строками", message)


class TestLoggingBehaviour(unittest.TestCase):
    def test_validation_log_record_contains_masked_password_only(self):
        with self.assertLogs("my_project", level="INFO") as context:
            validate_registration(VALID_LOGIN, VALID_PASSWORD, VALID_PASSWORD)
        output = "\n".join(context.output)
        self.assertIn(mask_password(VALID_PASSWORD), output)
        self.assertNotIn(VALID_PASSWORD, output)

    def test_rejected_registration_is_logged_as_warning(self):
        with self.assertLogs("my_project", level="WARNING") as context:
            validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(any(record.startswith("WARNING") for record in context.output))


if __name__ == "__main__":
    unittest.main()
