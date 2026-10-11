from abc import ABC, abstractmethod


class UserInterface(ABC):
    """
    Абстрактный базовый класс взаимодействия с пользователем.
    Выступает в роли интерфейса для получения входных данных.
    """

    @abstractmethod
    def get_registration_data(self) -> tuple:
        """Возвращает кортеж (login, password, confirm_password)."""


class ConsoleUserInterface(UserInterface):
    """Реализация интерфейса, запрашивающая данные через консоль (input)."""

    def get_registration_data(self) -> tuple:
        login = input("Введите логин: ")
        password = input("Введите пароль: ")
        confirm_password = input("Повторите пароль: ")
        return login, password, confirm_password