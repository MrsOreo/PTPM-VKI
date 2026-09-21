import os
import re
import sys
import logging
import hashlib

os.makedirs("logs", exist_ok=True)

log_format = "%(asctime)s | [%(levelname)-7s] | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/file_txt.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

BLACKLIST = {"admin", "root", "user", "test", "administrator", "guest", "system"}

PHONE_PATTERN = r"^\+\d-\d{3}-\d{3}-\d{4}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
STRING_LOGIN_PATTERN = r"^[a-zA-Z0-9_]{5,}$"
PASSWORD_ALLOWED_CHARS_PATTERN = r"^[а-яА-ЯёЁ0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]+$"
SPECIAL_CHARS_PATTERN = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]"


def mask_password(pwd: str) -> str:
    if not pwd:
        return "[MASKED:empty]"
    pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()[:8]
    return f"[MASKED:{pwd_hash}]"


def validate_registration(login: str, password: str, confirm_password: str) -> tuple:
    masked_pwd = mask_password(password)
    masked_confirm = mask_password(confirm_password)

    logger.info(f"Запрос валидации. Логин: '{login}', Пароль: {masked_pwd}, Подтверждение: {masked_confirm}")

    try:
        if password != confirm_password:
            msg = "Пароль и подтверждение пароля не совпадают."
            logger.warning(msg)
            return False, msg

        if len(password) < 7:
            msg = "Длина пароля должна быть не менее 7 символов."
            logger.warning(msg)
            return False, msg

        if not re.match(PASSWORD_ALLOWED_CHARS_PATTERN, password):
            msg = "Пароль содержит недопустимые символы. Разрешены только кириллица, цифры и спецсимволы."
            logger.warning(msg)
            return False, msg

        if not re.search(r"[А-ЯЁ]", password):
            msg = "Пароль должен содержать хотя бы одну заглавную букву кириллицы."
            logger.warning(msg)
            return False, msg

        if not re.search(r"[а-яё]", password):
            msg = "Пароль должен содержать хотя бы одну строчную букву кириллицы."
            logger.warning(msg)
            return False, msg

        if not re.search(r"\d", password):
            msg = "Пароль должен содержать хотя бы одну цифру."
            logger.warning(msg)
            return False, msg

        if not re.search(SPECIAL_CHARS_PATTERN, password):
            msg = "Пароль должен содержать хотя бы один спецсимвол."
            logger.warning(msg)
            return False, msg

        is_phone = bool(re.match(PHONE_PATTERN, login))
        is_email = bool(re.match(EMAIL_PATTERN, login))
        is_string = bool(re.match(STRING_LOGIN_PATTERN, login))

        if login.startswith("+") and not is_phone:
            msg = "Неверный формат телефона. Ожидаемый формат: +x-xxx-xxx-xxxx."
            logger.warning(msg)
            return False, msg

        if "@" in login and not is_email:
            msg = "Неверный формат email адреса."
            logger.warning(msg)
            return False, msg

        if not (is_phone or is_email or is_string):
            msg = "Неверный формат логина."
            logger.warning(msg)
            return False, msg

        if login.lower() in BLACKLIST:
            msg = f"Логин '{login}' находится в черном списке."
            logger.warning(msg)
            return False, msg

        logger.info("Валидация успешно пройдена.")
        return True, ""

    except Exception as e:
        error_msg = f"Произошла непредвиденная ошибка при валидации: {str(e)}"
        logger.error(error_msg)
        logger.exception("Трассировка стека исключения:")
        return False, error_msg


def main():
    logger.info("Приложение запущено.")

    test_cases = [
        ("user_test_01", "Пароль123!", "Пароль123!", "Успешная регистрация"),
        ("+7-999-123-4567", "СекретныйПароль2024@", "СекретныйПароль2024@", "Успешная регистрация (телефон)"),
        ("test@example.com", "МойПароль_99#", "МойПароль_99#", "Успешная регистрация (email)"),
        ("valid_login", "Пароль123!", "ДругойПароль1!", "Пароли не совпадают"),
        ("valid_login", "Пар1!", "Пар1!", "Длина пароля < 7"),
        ("valid_login", "Password123!", "Password123!", "Пароль содержит латиницу"),
        ("valid_login", "пароль123!", "пароль123!", "Нет заглавной буквы"),
        ("valid_login", "ПАРОЛЬ123!", "ПАРОЛЬ123!", "Нет строчной буквы"),
        ("valid_login", "Парольпароль!", "Парольпароль!", "Нет цифры"),
        ("valid_login", "Пароль123", "Пароль123", "Нет спецсимвола"),
        ("+7-99-123-4567", "Пароль123!", "Пароль123!", "Неверный формат телефона"),
        ("admin", "Пароль123!", "Пароль123!", "Логин в черном списке"),
        ("ab", "Пароль123!", "Пароль123!", "Логин < 5 символов"),
    ]

    for i, (login, pwd, confirm, desc) in enumerate(test_cases, 1):
        print(f"\n--- Тест {i}: {desc} ---")
        result, message = validate_registration(login, pwd, confirm)

        if result:
            print(f"Успех: {message if message else 'Данные корректны'}")
        else:
            print(f"Ошибка: {message}")

    logger.info("Приложение завершило работу.")


if __name__ == "__main__":
    main()