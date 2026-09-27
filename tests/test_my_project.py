import hashlib
import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from my_project import (
    LOGIN_MAX_LENGTH,
    LOGIN_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    RegistrationError,
    is_valid_email,
    is_valid_login,
    is_valid_password,
    is_valid_phone,
    normalize_email,
    normalize_phone,
    register_user,
    validate_registration,
)

VALID_LOGIN = "ivan_2024"
VALID_PASSWORD = "Passw0rd!"
VALID_PASSWORD_CONFIRM = "Passw0rd!"
VALID_EMAIL = "ivanov@mail.ru"
VALID_PHONE = "+79991234567"


class TestLoginValidation(unittest.TestCase):
    """Проверки правил валидации логина."""

    def test_login_with_acceptable_symbols_is_accepted(self):
        self.assertTrue(is_valid_login(VALID_LOGIN))

    def test_login_with_minimum_length_is_accepted(self):
        login = "a" * LOGIN_MIN_LENGTH
        self.assertTrue(is_valid_login(login))

    def test_login_with_maximum_length_is_accepted(self):
        login = "a" + "b" * (LOGIN_MAX_LENGTH - 1)
        self.assertTrue(is_valid_login(login))

    def test_login_surrounded_by_spaces_is_trimmed_and_accepted(self):
        self.assertTrue(is_valid_login("  " + VALID_LOGIN + "\n"))

    def test_login_starting_with_digit_is_rejected(self):
        self.assertFalse(is_valid_login("1ivan"))

    def test_login_starting_with_underscore_is_rejected(self):
        self.assertFalse(is_valid_login("_ivan"))

    def test_login_shorter_than_minimum_length_is_rejected(self):
        self.assertFalse(is_valid_login("a" * (LOGIN_MIN_LENGTH - 1)))

    def test_login_longer_than_maximum_length_is_rejected(self):
        self.assertFalse(is_valid_login("a" * (LOGIN_MAX_LENGTH + 1)))

    def test_login_with_cyrillic_letters_is_rejected(self):
        self.assertFalse(is_valid_login("иван"))

    def test_login_with_special_symbols_is_rejected(self):
        self.assertFalse(is_valid_login("ivan.petrov"))

    def test_empty_login_is_rejected(self):
        self.assertFalse(is_valid_login("   "))

    def test_login_of_non_string_type_is_rejected(self):
        for value in (None, 12345, ["ivan"]):
            with self.subTest(value=value):
                self.assertFalse(is_valid_login(value))


class TestPasswordValidation(unittest.TestCase):
    """Проверки требований к паролю."""

    def test_password_with_all_required_character_classes_is_accepted(self):
        self.assertTrue(is_valid_password(VALID_PASSWORD))

    def test_password_with_minimum_length_is_accepted(self):
        self.assertTrue(is_valid_password("Qw1!aaaa"))

    def test_password_with_maximum_length_is_accepted(self):
        self.assertTrue(is_valid_password("Aa1!" + "a" * (PASSWORD_MAX_LENGTH - 4)))

    def test_password_shorter_than_minimum_length_is_rejected(self):
        self.assertFalse(is_valid_password("Aa1!aaa"))

    def test_password_longer_than_maximum_length_is_rejected(self):
        self.assertFalse(is_valid_password("Aa1!" + "a" * (PASSWORD_MAX_LENGTH - 3)))

    def test_password_without_lowercase_letter_is_rejected(self):
        self.assertFalse(is_valid_password("PASSW0RD!"))

    def test_password_without_uppercase_letter_is_rejected(self):
        self.assertFalse(is_valid_password("passw0rd!"))

    def test_password_without_digit_is_rejected(self):
        self.assertFalse(is_valid_password("Password!"))

    def test_password_without_special_character_is_rejected(self):
        self.assertFalse(is_valid_password("Password1"))

    def test_password_with_unsupported_special_character_is_rejected(self):
        self.assertFalse(is_valid_password("Passw0rd?"))

    def test_password_of_non_string_type_is_rejected(self):
        for value in (None, 12345678):
            with self.subTest(value=value):
                self.assertFalse(is_valid_password(value))


class TestEmailValidation(unittest.TestCase):
    """Проверки правил валидации электронной почты."""

    def test_email_with_correct_domain_is_accepted(self):
        self.assertTrue(is_valid_email(VALID_EMAIL))

    def test_email_with_tags_and_subdomain_is_accepted(self):
        self.assertTrue(is_valid_email("ivan.petrov+tag@mail.example.com"))

    def test_email_surrounded_by_spaces_is_trimmed_and_accepted(self):
        self.assertTrue(is_valid_email("  " + VALID_EMAIL + "  "))

    def test_email_without_at_sign_is_rejected(self):
        self.assertFalse(is_valid_email("ivanovmail.ru"))

    def test_email_with_empty_domain_is_rejected(self):
        self.assertFalse(is_valid_email("ivanov@"))

    def test_email_without_domain_tld_is_rejected(self):
        self.assertFalse(is_valid_email("ivanov@mail."))

    def test_email_with_single_letter_tld_is_rejected(self):
        self.assertFalse(is_valid_email("ivanov@mail.c"))

    def test_email_with_double_dot_in_local_part_is_rejected(self):
        self.assertFalse(is_valid_email("ivan..petrov@mail.ru"))

    def test_email_with_cyrillic_domain_is_rejected(self):
        self.assertFalse(is_valid_email("ivanov@почта.рф"))

    def test_email_with_cyrillic_local_part_is_rejected(self):
        self.assertFalse(is_valid_email("иванов@mail.ru"))

    def test_email_with_domain_starting_with_hyphen_is_rejected(self):
        self.assertFalse(is_valid_email("ivanov@-mail.ru"))

    def test_email_with_too_long_local_part_is_rejected(self):
        self.assertFalse(is_valid_email("a" * 65 + "@mail.ru"))

    def test_email_of_non_string_type_is_rejected(self):
        for value in (None, 42):
            with self.subTest(value=value):
                self.assertFalse(is_valid_email(value))

    def test_email_longer_than_maximum_allowed_length_is_rejected(self):
        self.assertFalse(is_valid_email("a" * 60 + "@" + "b" * 200 + ".ru"))

    def test_normalize_email_of_non_string_type_returns_empty_string(self):
        self.assertEqual("", normalize_email(None))


class TestPhoneValidation(unittest.TestCase):
    """Проверки правил валидации номера телефона."""

    def test_phone_in_russian_international_format_is_accepted(self):
        self.assertTrue(is_valid_phone(VALID_PHONE))

    def test_phone_in_belarusian_international_format_is_accepted(self):
        self.assertTrue(is_valid_phone("+375991234567"))

    def test_phone_with_separators_is_accepted_and_normalized(self):
        self.assertTrue(is_valid_phone("+7 (999) 123-45-67"))
        self.assertEqual("+79991234567", normalize_phone("+7 (999) 123-45-67"))

    def test_phone_with_eight_placeholder_is_rejected(self):
        self.assertFalse(is_valid_phone("8 (999) 123-45-67"))

    def test_phone_without_plus_sign_is_rejected(self):
        self.assertFalse(is_valid_phone("79991234567"))

    def test_phone_with_too_few_digits_is_rejected(self):
        self.assertFalse(is_valid_phone("+7999123456"))

    def test_phone_with_too_many_digits_is_rejected(self):
        self.assertFalse(is_valid_phone("+799912345678"))

    def test_phone_with_wrong_country_code_is_rejected(self):
        self.assertFalse(is_valid_phone("+380991234567"))

    def test_phone_with_letters_inside_is_rejected(self):
        self.assertFalse(is_valid_phone("+7999A234567"))

    def test_empty_phone_is_rejected(self):
        self.assertFalse(is_valid_phone("+-() "))

    def test_phone_of_non_string_type_is_rejected(self):
        for value in (None, 79991234567):
            with self.subTest(value=value):
                self.assertFalse(is_valid_phone(value))

    def test_normalize_phone_of_non_string_type_returns_empty_string(self):
        self.assertEqual("", normalize_phone(None))


class TestValidateRegistration(unittest.TestCase):
    """Проверки комплексной валидации формы регистрации."""

    def test_fully_valid_data_produces_no_errors(self):
        errors = validate_registration(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
        )
        self.assertEqual({}, errors)

    def test_invalid_data_produces_error_for_every_field(self):
        errors = validate_registration("1", "pass", "other", "ivanov", "123")
        self.assertEqual(
            {"login", "password", "password_confirm", "email", "phone"},
            set(errors),
        )

    def test_errors_are_reported_as_non_empty_text(self):
        errors = validate_registration("1", "pass", "other", "ivanov", "123")
        for field, message in errors.items():
            with self.subTest(field=field):
                self.assertIsInstance(message, str)
                self.assertTrue(message)

    def test_password_confirmation_mismatch_is_reported(self):
        errors = validate_registration(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD + "1",
            VALID_EMAIL,
            VALID_PHONE,
        )
        self.assertIn("password_confirm", errors)
        self.assertNotIn("password", errors)

    def test_already_taken_login_is_reported(self):
        errors = validate_registration(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
            taken_logins={VALID_LOGIN},
        )
        self.assertIn("login", errors)

    def test_taken_login_is_compared_case_insensitively(self):
        errors = validate_registration(
            VALID_LOGIN.upper(),
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
            taken_logins={VALID_LOGIN},
        )
        self.assertIn("login", errors)

    def test_free_login_is_accepted_when_other_logins_are_taken(self):
        errors = validate_registration(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
            taken_logins={"petrov_2000", "sidorov_2001"},
        )
        self.assertNotIn("login", errors)

    def test_single_invalid_field_does_not_block_the_others(self):
        errors = validate_registration(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            "ivanov",
            VALID_PHONE,
        )
        self.assertEqual({"email"}, set(errors))


class TestRegisterUser(unittest.TestCase):
    """Проверки регистрации пользователя и формирования профиля."""

    def test_successful_registration_returns_normalized_profile(self):
        profile = register_user(
            "  " + VALID_LOGIN + "  ",
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            " " + VALID_EMAIL.upper() + " ",
            "+7 (999) 123-45-67",
        )
        self.assertEqual(VALID_LOGIN, profile["login"])
        self.assertEqual(VALID_EMAIL, profile["email"])
        self.assertEqual("+79991234567", profile["phone"])

    def test_password_is_stored_only_as_sha256_hash(self):
        profile = register_user(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
        )
        expected = hashlib.sha256(VALID_PASSWORD.encode("utf-8")).hexdigest()
        self.assertEqual(expected, profile["password_hash"])
        self.assertNotIn(VALID_PASSWORD, profile.values())
        self.assertNotIn("password", profile)

    def test_profile_contains_exactly_four_keys(self):
        profile = register_user(
            VALID_LOGIN,
            VALID_PASSWORD,
            VALID_PASSWORD_CONFIRM,
            VALID_EMAIL,
            VALID_PHONE,
        )
        self.assertEqual({"login", "email", "phone", "password_hash"}, set(profile))

    def test_registration_with_invalid_data_raises_registration_error(self):
        with self.assertRaises(RegistrationError) as context:
            register_user("1", "pass", "other", "ivanov", "123")
        self.assertEqual(
            {"login", "password", "password_confirm", "email", "phone"},
            set(context.exception.errors),
        )

    def test_registration_error_message_lists_all_problems(self):
        with self.assertRaises(RegistrationError) as context:
            register_user("1", "pass", "other", "ivanov", "123")
        message = str(context.exception)
        for field in ("login", "password", "email", "phone"):
            with self.subTest(field=field):
                self.assertIn(field, message)

    def test_registration_of_taken_login_raises_registration_error(self):
        with self.assertRaises(RegistrationError) as context:
            register_user(
                VALID_LOGIN,
                VALID_PASSWORD,
                VALID_PASSWORD_CONFIRM,
                VALID_EMAIL,
                VALID_PHONE,
                taken_logins={VALID_LOGIN},
            )
        self.assertIn("login", context.exception.errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
