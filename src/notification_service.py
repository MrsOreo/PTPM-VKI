from abc import ABC, abstractmethod


class NotificationService(ABC):
    """
    Абстрактный базовый класс сторонней зависимости.
    Выступает в роли интерфейса для отправки данных внешнему процессу
    (например, email-серверу).
    """

    @abstractmethod
    def send(self, result_message: str) -> bool:
        """Имитация передачи строки-результата стороннему процессу."""


class EmailNotificationService(NotificationService):
    """
    Имитация отправки данных на email-сервер.
    Внутри реализуется исключительно имитация передачи данных —
    реальная отправка не выполняется, сообщения лишь накапливаются.
    """

    def __init__(self):
        self.sent_messages = []

    def send(self, result_message: str) -> bool:
        self.sent_messages.append(result_message)
        return True