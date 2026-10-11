from database import RegistrationDatabase
from notification_service import NotificationService
from user_interface import UserInterface
from validator import RegistrationValidator


class RegistrationController:
    def __init__(
        self,
        validator: RegistrationValidator,
        database: RegistrationDatabase,
        user_interface: UserInterface,
        notifier: NotificationService,
    ):
        self.validator = validator
        self.database = database
        self.user_interface = user_interface
        self.notifier = notifier

    def register_user(self) -> tuple:
        login, password, confirm_password = self.user_interface.get_registration_data()

        record = self.database.get_record(login, password, confirm_password)

        if record is None:
            is_authorized, error_message = self.validator.validate(
                login, password, confirm_password
            )
            self.database.add_record(
                login, password, confirm_password, is_authorized, error_message
            )
        else:
            is_authorized = record["is_authorized"]
            error_message = record["error_message"]

        result_message = self._build_result(login, is_authorized, error_message)
        self.notifier.send(result_message)

        return is_authorized, error_message

    @staticmethod
    def _build_result(login: str, is_authorized: bool, error_message: str) -> str:
        if is_authorized:
            return f"Регистрация пользователя '{login}' прошла успешно."
        return f"Регистрация пользователя '{login}' отклонена: {error_message}"