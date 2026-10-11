from my_project import validate_registration


class RegistrationValidator:
    def validate(self, login: str, password: str, confirm_password: str) -> tuple:
        is_authorized, error_message = validate_registration(
            login, password, confirm_password
        )
        return is_authorized, error_message