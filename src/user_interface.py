from abc import ABC, abstractmethod


class UserInterface(ABC):
    @abstractmethod
    def get_registration_data(self) -> tuple:
        pass


class ConsoleUserInterface(UserInterface):
    def get_registration_data(self) -> tuple:
        login = input("Введите логин: ")
        password = input("Введите пароль: ")
        confirm_password = input("Повторите пароль: ")
        return login, password, confirm_password