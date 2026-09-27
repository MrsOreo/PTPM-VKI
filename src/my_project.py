import hashlib
import re
from typing import Any

LOGIN_MIN_LENGTH = 3
LOGIN_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 20
EMAIL_MAX_LENGTH = 254
EMAIL_LOCAL_MAX_LENGTH = 64

PASSWORD_SPECIAL_CHARS = "!@#$%^&*()-_=+"

LOGIN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
PASSWORD_LOWER_PATTERN = re.compile(r"[a-z]")
PASSWORD_UPPER_PATTERN = re.compile(r"[A-Z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(rf"[{re.escape(PASSWORD_SPECIAL_CHARS)}]")
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)
PHONE_PATTERN = re.compile(r"^\+(?:7\d{10}|375\d{9})$")

PHONE_SEPARATORS = " \t-()"

ERROR_LOGIN = "Логин: 3-20 символов, латиница, начинается с буквы, допустимы цифры и '_'"
ERROR_LOGIN_TAKEN = "Логин уже занят"
ERROR_PASSWORD = (
    "Пароль: 8-20 символов, минимум по одной строчной, прописной букве, цифре "
    "и спецсимволу из " + PASSWORD_SPECIAL_CHARS
)
ERROR_PASSWORD_CONFIRM = "Пароли не совпадают"
ERROR_EMAIL = "E-mail в формате user@example.com"
ERROR_PHONE = "Телефон в формате +79991234567 или +375991234567"


class RegistrationError(Exception):
    """Ошибка регистрации с перечнем проблемных полей."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__(
            "; ".join(f"{field}: {message}" for field, message in errors.items())
        )
        self.errors = errors


def normalize_phone(phone: Any) -> str:
    """Убирает пробелы и разделители из номера телефона."""
    if not isinstance(phone, str):
        return ""
    return "".join(char for char in phone.strip() if char not in PHONE_SEPARATORS)


def normalize_email(email: Any) -> str:
    """Убирает внешние пробелы и приводит адрес к нижнему регистру."""
    if not isinstance(email, str):
        return ""
    return email.strip().lower()


def is_valid_login(login: Any) -> bool:
    """Проверяет логин: 3-20 символов, латиница, первый символ - буква."""
    if not isinstance(login, str):
        return False
    candidate = login.strip()
    if not LOGIN_MIN_LENGTH <= len(candidate) <= LOGIN_MAX_LENGTH:
        return False
    return LOGIN_PATTERN.fullmatch(candidate) is not None


def is_valid_password(password: Any) -> bool:
    """Проверяет пароль: 8-20 символов и все четыре обязательных класса символов."""
    if not isinstance(password, str):
        return False
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return False
    required = (
        PASSWORD_LOWER_PATTERN,
        PASSWORD_UPPER_PATTERN,
        PASSWORD_DIGIT_PATTERN,
        PASSWORD_SPECIAL_PATTERN,
    )
    return all(pattern.search(password) for pattern in required)


def is_valid_email(email: Any) -> bool:
    """Проверяет адрес электронной почты."""
    if not isinstance(email, str):
        return False
    candidate = email.strip()
    if len(candidate) > EMAIL_MAX_LENGTH:
        return False
    if len(candidate.split("@")[0]) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    return EMAIL_PATTERN.fullmatch(candidate) is not None


def is_valid_phone(phone: Any) -> bool:
    """Проверяет номер телефона в международном формате."""
    if not isinstance(phone, str):
        return False
    return PHONE_PATTERN.fullmatch(normalize_phone(phone)) is not None


def validate_registration(
    login: Any,
    password: Any,
    password_confirm: Any,
    email: Any,
    phone: Any,
    taken_logins: set[str] | None = None,
) -> dict[str, str]:

    errors: dict[str, str] = {}

    if not is_valid_login(login):
        errors["login"] = ERROR_LOGIN
    else:
        occupied = {item.strip().lower() for item in (taken_logins or set())}
        if login.strip().lower() in occupied:
            errors["login"] = ERROR_LOGIN_TAKEN

    if not is_valid_password(password):
        errors["password"] = ERROR_PASSWORD

    if not isinstance(password, str) or password != password_confirm:
        errors["password_confirm"] = ERROR_PASSWORD_CONFIRM

    if not is_valid_email(email):
        errors["email"] = ERROR_EMAIL

    if not is_valid_phone(phone):
        errors["phone"] = ERROR_PHONE

    return errors


def register_user(
    login: Any,
    password: Any,
    password_confirm: Any,
    email: Any,
    phone: Any,
    taken_logins: set[str] | None = None,
) -> dict[str, Any]:

    errors = validate_registration(
        login, password, password_confirm, email, phone, taken_logins
    )
    if errors:
        raise RegistrationError(errors)

    return {
        "login": login.strip(),
        "email": normalize_email(email),
        "phone": normalize_phone(phone),
        "password_hash": hashlib.sha256(password.encode("utf-8")).hexdigest(),
    }
